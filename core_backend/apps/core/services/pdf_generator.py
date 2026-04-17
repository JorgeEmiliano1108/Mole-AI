# =============================================================================
# Copyright (C) 2024-2026 Mole.AI — All Rights Reserved.
#
# AVISO DE PROPIEDAD INTELECTUAL:
# Este archivo es propiedad exclusiva de Mole.AI y sus autores originales.
# Queda estrictamente prohibida la copia, modificación, distribución,
# sublicenciamiento o uso comercial de este código, total o parcialmente,
# sin la autorización expresa y por escrito de los titulares del Copyright.
#
# Cualquier uso no autorizado será perseguido conforme a la Ley Federal
# del Derecho de Autor (México) y tratados internacionales aplicables.
# =============================================================================
"""
PDF generator for AIDiagnostic reports using ReportLab.

Produces a branded one-page (or multi-page) PDF containing:
  • Logo + header
  • Diagnostic metadata (id, plant, date, label, confidence)
  • Sensor readings (or a clear "no data" fallback)

Usage::

    from apps.core.services.pdf_generator import generate_diagnostic_pdf
    pdf_bytes = generate_diagnostic_pdf(diagnostic_id)
"""
import io
import logging
import os
from uuid import UUID

import httpx

from django.conf import settings
from django.contrib.staticfiles import finders

from reportlab.lib import colors
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.units import mm, cm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT

logger = logging.getLogger(__name__)

# ── LLM Summary (reuses FastAPI's loaded model — no local LLM in Django) ────
_FASTAPI_LLM_URL = os.getenv(
    "FASTAPI_SUMMARY_URL",
    "http://fastapi_rag:8002/api/v1/mole-ai/chat",
)
_MOLE_AI_API_KEY = os.getenv("MOLE_AI_API_KEY", "")

_SUMMARY_FALLBACK = (
    "No fue posible generar un resumen automático en este momento. "
    "Consulte los datos del diagnóstico y las lecturas de sensor para su análisis."
)


def request_summary(diagnostic_data: dict) -> str:
    """Ask the FastAPI LLM for a 3-paragraph phytosanitary summary.

    Makes a synchronous HTTP POST (Django runs in sync context). Uses a
    10-second timeout and returns a generic fallback on any failure so the
    PDF is always generated.
    """
    prompt = (
        "Eres un agrónomo experto redactando reportes fitosanitarios. "
        "Con base en los siguientes datos de diagnóstico, genera un resumen ejecutivo "
        "de exactamente 3 párrafos en español. "
        "Párrafo 1: estado general de la planta. "
        "Párrafo 2: hallazgos del diagnóstico y confianza. "
        "Párrafo 3: recomendaciones de acción.\n\n"
        f"Datos: {diagnostic_data}"
    )
    try:
        headers = {}
        if _MOLE_AI_API_KEY:
            headers["X-API-Key"] = _MOLE_AI_API_KEY
        resp = httpx.post(
            _FASTAPI_LLM_URL,
            json={"question": prompt},
            headers=headers,
            timeout=httpx.Timeout(connect=3.0, read=10.0, write=3.0, pool=3.0),
        )
        resp.raise_for_status()
        data = resp.json()
        return str(data.get("answer") or data.get("response") or _SUMMARY_FALLBACK)
    except Exception as exc:
        logger.warning("LLM summary request failed: %s — using fallback text.", exc)
        return _SUMMARY_FALLBACK

# ── Styles ───────────────────────────────────────────────────────────────────
_styles = getSampleStyleSheet()
_TITLE_STYLE = ParagraphStyle(
    "DiagTitle",
    parent=_styles["Heading1"],
    fontSize=18,
    spaceAfter=6 * mm,
    alignment=TA_CENTER,
    textColor=colors.HexColor("#2E7D32"),
)
_SUBTITLE_STYLE = ParagraphStyle(
    "DiagSubtitle",
    parent=_styles["Heading2"],
    fontSize=13,
    spaceBefore=6 * mm,
    spaceAfter=3 * mm,
    textColor=colors.HexColor("#33691E"),
)
_BODY_STYLE = ParagraphStyle(
    "DiagBody",
    parent=_styles["Normal"],
    fontSize=10,
    leading=14,
)
_SMALL_STYLE = ParagraphStyle(
    "DiagSmall",
    parent=_styles["Normal"],
    fontSize=8,
    textColor=colors.grey,
    alignment=TA_CENTER,
)


def _resolve_logo_path() -> str | None:
    """Return the absolute filesystem path to the project logo, or None."""
    # 1. Try staticfiles finders (works with WHITENOISE_USE_FINDERS=True)
    result = finders.find("assets/topo.png")
    if result and isinstance(result, str):
        return result

    # 2. Fallback: manual STATICFILES_DIRS lookup
    import os
    for static_dir in getattr(settings, "STATICFILES_DIRS", []):
        candidate = os.path.join(str(static_dir), "assets", "topo.png")
        if os.path.isfile(candidate):
            return candidate

    logger.warning("Logo not found in static assets; PDF will be generated without logo.")
    return None


def _build_header(logo_path: str | None) -> list:
    """Return flowable elements for the top header."""
    elements: list = []
    if logo_path:
        try:
            logo = Image(logo_path, width=30 * mm, height=30 * mm)
            logo.hAlign = "CENTER"
            elements.append(logo)
            elements.append(Spacer(1, 3 * mm))
        except Exception:
            logger.warning("Could not load logo image at %s", logo_path)
    elements.append(Paragraph("Mole AI — Reporte de Diagnóstico", _TITLE_STYLE))
    elements.append(Spacer(1, 2 * mm))
    return elements


def _kv_table(rows: list[tuple[str, str]]) -> Table:
    """Build a two-column key/value table with styling."""
    data = [[Paragraph(f"<b>{k}</b>", _BODY_STYLE), Paragraph(str(v), _BODY_STYLE)] for k, v in rows]
    t = Table(data, colWidths=[55 * mm, 120 * mm])
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#E8F5E9")),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#C8E6C9")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    return t


def generate_diagnostic_pdf(diagnostic_id: UUID | str) -> bytes:
    """Generate a PDF report for the given ``AIDiagnostic`` id.

    Returns the PDF as raw ``bytes`` ready to be wrapped in a
    ``FileResponse`` / ``HttpResponse``.

    Raises ``AIDiagnostic.DoesNotExist`` if the id is invalid.
    """
    # Late import to avoid circular / AppRegistry issues at module level.
    from apps.core.models import AIDiagnostic, SensorLog

    diagnostic = AIDiagnostic.objects.get(pk=diagnostic_id)

    # ── Sensor data (fail-safe) ──────────────────────────────────────────
    sensor_log = (
        SensorLog.objects.filter(plant_id=diagnostic.plant_id)
        .order_by("-recorded_at")
        .first()
    )

    # ── Build PDF ────────────────────────────────────────────────────────
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=LETTER,
        topMargin=20 * mm,
        bottomMargin=15 * mm,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
    )

    logo_path = _resolve_logo_path()
    elements: list = _build_header(logo_path)

    # ── Diagnostic info ──────────────────────────────────────────────────
    elements.append(Paragraph("Información del Diagnóstico", _SUBTITLE_STYLE))

    meta = diagnostic.metadata if isinstance(diagnostic.metadata, dict) else {}

    diag_rows: list[tuple[str, str]] = [
        ("ID", str(diagnostic.id)),
        ("Planta", str(diagnostic.plant_id)),
        ("Fecha", diagnostic.analyzed_at.strftime("%d/%m/%Y %H:%M") if diagnostic.analyzed_at else "—"),
        ("Diagnóstico", diagnostic.diagnosis_label or meta.get("condition", "—")),
        ("Confianza", f"{(diagnostic.confidence_score or 0) * 100:.1f} %"),
    ]

    # Optional fields that may exist on extended models
    severity = meta.get("severity") or getattr(diagnostic, "severity", None)
    if severity:
        diag_rows.append(("Severidad", str(severity).capitalize()))

    description = meta.get("description") or getattr(diagnostic, "condition_description", None)
    if description:
        diag_rows.append(("Descripción", str(description)))

    model_used = meta.get("model_used") or getattr(diagnostic, "ai_model_used", None)
    if model_used:
        diag_rows.append(("Modelo IA", str(model_used)))

    elements.append(_kv_table(diag_rows))
    elements.append(Spacer(1, 6 * mm))

    # ── Sensor readings ──────────────────────────────────────────────────
    elements.append(Paragraph("Lecturas de Sensor", _SUBTITLE_STYLE))

    if sensor_log is None:
        elements.append(
            Paragraph(
                "⚠ Datos de sensor no disponibles — el dispositivo IoT no registró "
                "lecturas recientes para esta planta.",
                _BODY_STYLE,
            )
        )
    else:
        sensor_rows: list[tuple[str, str]] = [
            ("Fecha lectura", sensor_log.recorded_at.strftime("%d/%m/%Y %H:%M") if sensor_log.recorded_at else "—"),
            ("Humedad suelo", f"{sensor_log.soil_humidity:.1f} %" if sensor_log.soil_humidity is not None else "—"),
            ("Temperatura aire", f"{sensor_log.air_temperature:.1f} °C" if sensor_log.air_temperature is not None else "—"),
            ("Índice UV", f"{sensor_log.uv_index:.1f}" if sensor_log.uv_index is not None else "—"),
            ("Nivel de luz", f"{sensor_log.light_level:.0f} lux" if sensor_log.light_level is not None else "—"),
        ]
        # ph_level may exist on extended wide-table schemas
        ph = getattr(sensor_log, "ph_level", None)
        if ph is not None:
            sensor_rows.append(("pH", f"{ph:.2f}"))
        elements.append(_kv_table(sensor_rows))

    elements.append(Spacer(1, 10 * mm))

    # ── Executive summary (generated by FastAPI LLM) ─────────────────────
    elements.append(Paragraph("Resumen Ejecutivo", _SUBTITLE_STYLE))

    summary_input = {
        "diagnostic_id": str(diagnostic.id),
        "plant_id": str(diagnostic.plant_id),
        "diagnosis": diagnostic.diagnosis_label or meta.get("condition", "—"),
        "confidence": f"{(diagnostic.confidence_score or 0) * 100:.1f}%",
        "severity": severity or "—",
        "description": description or "—",
        "sensor_available": sensor_log is not None,
    }
    if sensor_log is not None:
        summary_input["soil_humidity"] = sensor_log.soil_humidity
        summary_input["air_temperature"] = sensor_log.air_temperature

    summary_text = request_summary(summary_input)
    elements.append(Paragraph(summary_text, _BODY_STYLE))
    elements.append(Spacer(1, 8 * mm))

    # ── Footer ───────────────────────────────────────────────────────────
    elements.append(
        Paragraph(
            "Generado automáticamente por Mole AI. Este reporte no sustituye el criterio de un profesional agrónomo.",
            _SMALL_STYLE,
        )
    )

    doc.build(elements)
    return buf.getvalue()
