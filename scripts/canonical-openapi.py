"""Gate estructural del contrato móvil (issue 11).

Compara el schema OpenAPI regenerado desde el código contra el snapshot
versionado IGNORANDO metadatos cosméticos (description/summary/tags/examples):
solo importan paths, métodos, operationId, parámetros (nombre/vía/requerido)
y códigos de respuesta. Las descripciones a mano del snapshot se preservan
intacto — jamás se regenera el archivo.

Regla de respuestas: el snapshot puede documentar códigos adicionales que el
análisis estático no infiere (p. ej. 403 fail-closed dinámicos); solo falla si
al código le falta algo documentado como existente... en realidad al revés:
falla si el CÓDIGO expone algo que el snapshot NO documenta (path, método,
operationId, parámetro o código de respuesta ausentes en snapshot).

Uso: canonical-openapi.py REGENERADO SNAPSHOT
Exit 0 = sin drift estructural. Exit 1 = drift (imprime detalle).
"""
from __future__ import annotations

import sys

import yaml


def norm_path(path: str) -> str:
    """Normaliza `/x` y `/x/` como el mismo path (convención del snapshot)."""
    if len(path) > 1 and path.endswith("/"):
        return path[:-1]
    return path


def canonical_operation(op: dict) -> dict:
    params = sorted(
        (p.get("name"), p.get("in"), bool(p.get("required")))
        for p in op.get("parameters", []) or []
    )
    return {
        "operationId": op.get("operationId"),
        "parameters": params,
        "responses": sorted(str(k) for k in (op.get("responses") or {})),
    }


def load_canonical(path: str) -> dict:
    with open(path, encoding="utf-8") as fh:
        doc = yaml.safe_load(fh)
    out = {}
    for raw_path, methods in (doc.get("paths") or {}).items():
        for method, op in methods.items():
            if isinstance(op, dict):
                out[(norm_path(raw_path), method)] = canonical_operation(op)
    return out


def main() -> int:
    regen_path, snapshot_path = sys.argv[1], sys.argv[2]
    regen = load_canonical(regen_path)
    snap = load_canonical(snapshot_path)

    failures: list[str] = []
    for key in sorted(set(regen) | set(snap)):
        path, method = key
        if key not in snap:
            failures.append(
                f"+ {method.upper()} {path} FALTA en snapshot "
                f"(operationId={regen[key]['operationId']})"
            )
            continue
        if key not in regen:
            failures.append(f"- {method.upper()} {path} muerto en snapshot (ya no existe en código)")
            continue
        r, s = regen[key], snap[key]
        if r["operationId"] != s["operationId"]:
            failures.append(f"~ {method.upper()} {path} operationId: código={r['operationId']} snapshot={s['operationId']}")
        if r["parameters"] != s["parameters"]:
            failures.append(f"~ {method.upper()} {path} parámetros difieren")
        missing_codes = [c for c in r["responses"] if c not in s["responses"]]
        if missing_codes:
            failures.append(
                f"~ {method.upper()} {path} códigos sin documentar en snapshot: {missing_codes}"
            )

    if failures:
        print("[FAIL] Drift estructural del contrato:")
        for line in failures:
            print(f"  {line}")
        print("Actualiza docs/contracts/openapi.yml a mano (descripciones intactas) "
              "y documenta el cambio en issues/11-contrato-movil-congelado.md.")
        return 1
    print(f"[OK] Contrato estructural sin drift ({len(regen)} operaciones).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
