# =============================================================================
# Copyright (C) 2024-2026 Mole.AI — All Rights Reserved.
# =============================================================================
"""SafetyValidator — dominio legal para agroquímicos y NOM-059-SEMARNAT.

Actúa como gate fail-closed: si no hay datos de seguridad y la directriz
`fallback_block_when_data_missing` está activa, cualquier evaluación se
rechaza con código 403. Los archivos JSON se validan contra
`docs/safety/schema.json` en carga para garantizar que el contrato se cumple.
"""
from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path
from typing import Any, Self

import jsonschema
import yaml
from django.conf import settings


class SafetyResult(dict):
    """Resultado inmutable-ish de una validación de seguridad."""

    def __init__(
        self,
        *,
        safe: bool,
        code: str,
        reason: str | None = None,
        status_code: int = 200,
    ):
        super().__init__(safe=safe, code=code, reason=reason, status_code=status_code)

    @property
    def safe(self) -> bool:  # type: ignore[override]
        return bool(self["safe"])

    @property
    def code(self) -> str:  # type: ignore[override]
        return str(self["code"])

    @property
    def reason(self) -> str | None:  # type: ignore[override]
        return self["reason"]

    @property
    def status_code(self) -> int:  # type: ignore[override]
        return int(self["status_code"])

    @classmethod
    def ok(cls) -> SafetyResult:
        return cls(safe=True, code="SAFETY_OK")


class SafetyValidator:
    """Singleton fail-closed para validación de dominio legal."""

    _instance: SafetyValidator | None = None

    def __new__(cls) -> Self:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load()
        return cls._instance

    @classmethod
    def reset(cls) -> None:
        """Principalmente para tests que necesitan forzar recarga."""
        cls._instance = None

    def _project_root(self) -> Path:
        return Path(settings.BASE_DIR).parent

    def _load(self) -> None:
        root = self._project_root()
        schema_path = root / "docs" / "safety" / "schema.json"
        limits_path = root / "docs" / "safety" / "agrochemical_limits.json"
        species_path = root / "docs" / "safety" / "nom059_species.json"
        rules_path = root / "safety_rules.yaml"

        self.schema = json.loads(schema_path.read_text(encoding="utf-8"))

        limits = json.loads(limits_path.read_text(encoding="utf-8"))
        jsonschema.validate(limits, self.schema)
        self.agrochemicals: dict[str, dict[str, Any]] = {
            item["id"]: item for item in limits
        }

        species = json.loads(species_path.read_text(encoding="utf-8"))
        jsonschema.validate(species, self.schema)
        self.nom059: dict[str, dict[str, Any]] = {
            item["id"]: item for item in species
        }

        self.rules = yaml.safe_load(rules_path.read_text(encoding="utf-8"))

    @property
    def _block_code(self) -> int:
        return int(self.rules.get("directives", {}).get("safety_response_code", 403))

    @property
    def _fallback_block(self) -> bool:
        return bool(
            self.rules.get("directives", {}).get("fallback_block_when_data_missing", True)
        )

    @staticmethod
    def _normalize(text: str | None) -> str:
        if text is None:
            return ""
        cleaned = (
            unicodedata.normalize("NFKD", text)
            .encode("ASCII", "ignore")
            .decode("ASCII")
            .lower()
        )
        return re.sub(r"[^a-z0-9\s]", " ", cleaned)

    def _tokenize(self, text: str | None) -> set[str]:
        return set(self._normalize(text).split())

    def check_nom059_violation(self, text: str | None) -> SafetyResult:
        """Detecta si un texto menciona una especie protegida por NOM-059."""
        if not text:
            return SafetyResult.ok()

        tokens = self._tokenize(text)
        for item in self.nom059.values():
            names = {self._normalize(item["scientific_name"])}
            names.update(self._normalize(n) for n in item.get("common_names", []))
            for name in names:
                # Coincidencia por palabra/frase completa, evitando falsos positivos
                # parciales como 'pey' dentro de 'peyote'.
                pattern = r"(?:^|\s)" + re.escape(name) + r"(?:$|\s|s)"
                if re.search(pattern, self._normalize(text)) or name in tokens:
                    return SafetyResult(
                        safe=False,
                        code="SAFETY_NOM059_PROTECTED",
                        reason=str(item.get("warning")),
                        status_code=self._block_code,
                    )
        return SafetyResult.ok()

    def validate_agrochemical(
        self,
        agrochemical_id: str | None,
        dose_per_hectare: float | None = None,
        applications: int | None = None,
        crop: str | None = None,
        region: str | None = None,
        combination_ids: list[str] | None = None,
    ) -> SafetyResult:
        """Valida que la prescripción de un agroquímico esté dentro de los
        umbrales regulatorios y no esté en cultivos/regiones prohibidas."""
        if not agrochemical_id:
            return SafetyResult.ok()

        agro = self.agrochemicals.get(agrochemical_id)
        if agro is None:
            if self._fallback_block:
                return SafetyResult(
                    safe=False,
                    code="SAFETY_DATA_MISSING",
                    reason="Agroquímico no catalogado; bloqueado por política.",
                    status_code=self._block_code,
                )
            return SafetyResult.ok()

        if self.rules.get("directives", {}).get("block_on_max_dose_exceeded", True) and dose_per_hectare is not None:
            max_dose = agro.get("max_dose_per_hectare")
            if max_dose is not None and dose_per_hectare > max_dose:
                return SafetyResult(
                    safe=False,
                    code="SAFETY_DOSE_EXCEEDED",
                    reason=f"Dosis {dose_per_hectare} {agro.get('unit')} excede "
                           f"el máximo de {max_dose} {agro.get('unit')}.",
                    status_code=self._block_code,
                )

        if self.rules.get("directives", {}).get("block_on_max_applications_exceeded", True) and applications is not None:
            max_apps = agro.get("max_applications_per_cycle")
            if max_apps is not None and applications > max_apps:
                return SafetyResult(
                    safe=False,
                    code="SAFETY_APPLICATIONS_EXCEEDED",
                    reason=f"Aplicaciones ({applications}) exceden el máximo "
                           f"permitido ({max_apps}).",
                    status_code=self._block_code,
                )

        if self.rules.get("directives", {}).get("block_on_restricted_crop", True) and crop:
            restricted = {self._normalize(c) for c in agro.get("restricted_crops", [])}
            if self._normalize(crop) in restricted:
                return SafetyResult(
                    safe=False,
                    code="SAFETY_RESTRICTED_CROP",
                    reason=f"Cultivo '{crop}' restringido para este agroquímico.",
                    status_code=self._block_code,
                )

        region_forbidden = {
            self._normalize(r)
            for r in self.rules.get("forbidden_regions_global", [])
        }
        if region:
            if self._normalize(region) in region_forbidden:
                return SafetyResult(
                    safe=False,
                    code="SAFETY_FORBIDDEN_REGION",
                    reason=f"Región '{region}' bloqueada globalmente.",
                    status_code=self._block_code,
                )
            local_forbidden = {
                self._normalize(r) for r in agro.get("forbidden_regions", [])
            }
            if self._normalize(region) in local_forbidden:
                return SafetyResult(
                    safe=False,
                    code="SAFETY_FORBIDDEN_REGION",
                    reason=f"Región '{region}' restringida para este agroquímico.",
                    status_code=self._block_code,
                )

        if self.rules.get("directives", {}).get("block_on_unauthorized_combination", True):
            combo_ids = set(combination_ids or [])
            combo_ids.add(agrochemical_id)
            for combo in self.rules.get("unauthorized_combinations", []):
                combo_set = set(combo.get("agrochemical_ids", []))
                if combo_set and combo_set.issubset(combo_ids):
                    return SafetyResult(
                        safe=False,
                        code="SAFETY_UNAUTHORIZED_COMBINATION",
                        reason=str(combo.get("reason", "Combinación no autorizada.")),
                        status_code=self._block_code,
                    )

        return SafetyResult.ok()

    def validate(self, payload: dict[str, Any]) -> SafetyResult:
        """Punto de entrada genérico. Evalua texto NOM-059 y agroquímicos."""
        text = payload.get("text") or payload.get("reason") or payload.get("pvu_reason")
        result = self.check_nom059_violation(text)
        if not result.safe:
            return result

        agro_id = payload.get("agrochemical_id")
        if agro_id:
            result = self.validate_agrochemical(
                agrochemical_id=str(agro_id),
                dose_per_hectare=payload.get("dose_per_hectare"),
                applications=payload.get("applications"),
                crop=payload.get("crop"),
                region=payload.get("region"),
                combination_ids=payload.get("combination_ids"),
            )
            if not result.safe:
                return result

        return SafetyResult.ok()
