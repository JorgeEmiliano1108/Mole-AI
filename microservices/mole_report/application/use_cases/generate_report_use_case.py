import io
import logging
import traceback
from datetime import datetime
from infrastructure.redis.job_metadata_store import JobMetadataStore
from infrastructure.llm.nvidia_client import NvidiaReportClient
from infrastructure.db.supabase_client import SupabaseClient
from infrastructure.storage.s3_adapter import S3Adapter
from application.services.report_builder import ReportBuilder
from app.config import settings
from infrastructure.pdf.weasyprint_report_generator import WeasyPrintReportGenerator

logger = logging.getLogger(__name__)


class GenerateReportUseCase:
    def __init__(self):
        self.job_store = JobMetadataStore.from_env()
        self.nim = NvidiaReportClient.from_env()
        self.supabase = SupabaseClient.from_env()

    def _detect_anomalies(self, logs: list) -> list:
        # Simple statistical anomaly detection: points outside mean +/- 2*std
        import math

        values = [float(r.get("value", 0)) for r in logs if r.get("value") is not None]
        if not values:
            return []
        mean = sum(values) / len(values)
        var = sum((v - mean) ** 2 for v in values) / len(values)
        std = math.sqrt(var)
        threshold_high = mean + 2 * std
        threshold_low = mean - 2 * std
        anomalies = [r for r in logs if float(r.get("value", 0)) > threshold_high or float(r.get("value", 0)) < threshold_low]
        return anomalies

    def run(self, payload: dict, job_id: str) -> None:
        start_ts = datetime.utcnow().isoformat() + "Z"
        try:
            self.job_store.update_status(job_id, "STARTED")
            self.job_store.set_progress(job_id, 5)

            # 1) CAG: fetch historical logs for 30/60/90 days
            logs_30 = self.supabase.fetch_sensor_logs(days=30, sensors=payload.get("sensors", []))
            logs_60 = self.supabase.fetch_sensor_logs(days=60, sensors=payload.get("sensors", []))
            logs_90 = self.supabase.fetch_sensor_logs(days=90, sensors=payload.get("sensors", []))
            # merge or keep as needed; for LLM we'll provide a combined view
            combined_logs = (logs_30 or []) + (logs_60 or []) + (logs_90 or [])
            self.job_store.set_progress(job_id, 25)

            # Basic anomaly detection
            anomalies = self._detect_anomalies(combined_logs)
            self.job_store.set_progress(job_id, 40)

            # 2) NVIDIA NIM: Synthesize insights from telemetry
            insights = self.nim.synthesize_insights(docs=[], logs=combined_logs)
            self.job_store.set_progress(job_id, 75)

            # 3) Build HTML report
            builder = ReportBuilder()
            html = builder.build_report_html(logs=combined_logs, insights=insights)
            # ensure disclaimer present
            _COFEPRIS_DISCLAIMER = (
                '<footer style="border-top:1px solid #ccc;margin-top:20px;padding-top:10px;font-size:10px;">'
                "<strong>AVISO LEGAL — COFEPRIS:</strong> La información contenida en este reporte es de carácter "
                "estrictamente informativo y no constituye una recomendación profesional, receta agronómica ni "
                "prescripción de uso de plaguicidas o agroquímicos. Cualquier aplicación de productos "
                "fitosanitarios debe realizarse bajo la supervisión de un profesional certificado y conforme a "
                "las disposiciones de la Comisión Federal para la Protección contra Riesgos Sanitarios (COFEPRIS), "
                "la Ley General de Salud, el Reglamento en Materia de Registros, Autorizaciones de Importación y "
                "Exportación y Certificados de Exportación de Plaguicidas, Nutrientes Vegetales y Sustancias y "
                "Materiales Tóxicos o Peligrosos, y demás normativa aplicable. Mole.AI no se hace responsable "
                "por el uso indebido de la información aquí presentada."
                "</footer>"
            )
            if "COFEPRIS" not in html:
                html += _COFEPRIS_DISCLAIMER
            self.job_store.set_progress(job_id, 85)

            # 5) Render PDF in-memory — ZERO DISK I/O
            pdf_buffer = io.BytesIO()
            pdf_bytes = WeasyPrintReportGenerator.generate_pdf(html)
            pdf_buffer.write(pdf_bytes)
            pdf_buffer.seek(0)
            self.job_store.set_progress(job_id, 92)

            # 6) Upload raw bytes to S3 — NO local file write
            filename = f"report_{job_id}.pdf"
            s3_key = f"reports/{filename}"
            s3 = S3Adapter.from_env()
            s3.upload_bytes(pdf_buffer.read(), s3_key)
            presigned_url = s3.generate_presigned_url(s3_key, expires_in=86400)  # 24h

            self.job_store.set_result(job_id, presigned_url)
            self.job_store.update_job(job_id, {"pdf_s3_path": s3_key})
            self.job_store.set_progress(job_id, 100)
            self.job_store.update_status(job_id, "SUCCESS")
            logger.info(f"Reporte generado y subido a S3: {s3_key}")

            # 7) Audit: persist to Supabase audit table `reports_audit`
            try:
                audit_payload = {
                    "job_id": job_id,
                    "status": "SUCCESS",
                    "s3_path": public_url,
                    "started_at": start_ts,
                    "finished_at": datetime.utcnow().isoformat() + "Z",
                }
                self.supabase.insert_audit_record("reports_audit", audit_payload)
            except Exception:
                logger.exception("Failed to persist audit record (non-fatal)")

        except Exception as exc:  # pragma: no cover - top-level orchestration
            tb = traceback.format_exc()
            sanitized = tb[-2000:]
            self.job_store.set_error(job_id, sanitized)
            self.job_store.update_status(job_id, "FAILED")
            # try to persist failure audit
            try:
                audit_payload = {
                    "job_id": job_id,
                    "status": "FAILED",
                    "s3_path": None,
                    "error_message": sanitized,
                    "started_at": start_ts,
                    "finished_at": datetime.utcnow().isoformat() + "Z",
                }
                self.supabase.insert_audit_record("reports_audit", audit_payload)
            except Exception:
                logger.exception("Failed to persist failure audit (ignored)")
            raise