import logging
import traceback
from datetime import datetime
from infrastructure.redis.job_metadata_store import JobMetadataStore
from infrastructure.db.supabase_client import SupabaseClient
from infrastructure.faiss.faiss_reader_adapter import FAISSReaderAdapter
from infrastructure.llm.huggingface_client import HuggingFaceClient
from infrastructure.storage.s3_adapter import S3Adapter
from application.services.report_builder import ReportBuilder
from app.config import settings
from infrastructure.pdf.weasyprint_report_generator import WeasyPrintReportGenerator

logger = logging.getLogger(__name__)


class GenerateReportUseCase:
    def __init__(self):
        self.job_store = JobMetadataStore.from_env()
        self.supabase = SupabaseClient.from_env()
        self.hf = HuggingFaceClient.from_env()

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

            # 2) RAG: query FAISS using anomaly snippets
            docs = []
            with FAISSReaderAdapter() as faiss:
                if anomalies:
                    # build queries from anomaly sensor names / values
                    for a in anomalies[:10]:
                        q = f"anomaly sensor {a.get('sensor')} value {a.get('value')}"
                        docs.extend(faiss.query(q, top_k=3))
                else:
                    docs = faiss.query("general plant health anomalies", top_k=5)

            # deduplicate docs by source/text
            seen = set()
            unique_docs = []
            for d in docs:
                key = (d.get("meta", {}).get("source"), d.get("text", "")[:200])
                if key in seen:
                    continue
                seen.add(key)
                unique_docs.append(d)

            self.job_store.set_progress(job_id, 55)

            # 3) LLM: synthesize insights with prompt instructing Agronomist role
            insights = self.hf.synthesize_insights(unique_docs, combined_logs)
            self.job_store.set_progress(job_id, 75)

            # 4) Build report: figures + HTML (include COFEPRIS disclaimer in footer)
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

            # 5) Render PDF
            pdf_bytes = WeasyPrintReportGenerator.generate_pdf(html)
            self.job_store.set_progress(job_id, 95)

            # 6) Upload PDF to local volume
            import os
            reports_dir = "/app/media/reports"
            os.makedirs(reports_dir, exist_ok=True)
            local_path = os.path.join(reports_dir, f"{job_id}.pdf")
            with open(local_path, "wb") as f:
                f.write(pdf_bytes)
            
            public_url = f"/static/reports/{job_id}.pdf"
            self.job_store.set_result(job_id, public_url)
            self.job_store.set_progress(job_id, 100)
            self.job_store.update_status(job_id, "SUCCESS")

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
