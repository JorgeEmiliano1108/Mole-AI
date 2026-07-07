"""
Infrastructure Layer - NVIDIA NIM LLM Client for Report Synthesis
Model: meta/llama-3.3-70b-instruct
"""
import logging
from typing import List, Dict

from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception

from app.config import settings

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = (
    "Eres un Ingeniero Agrónomo experto. Recibirás telemetría de sensores de campo "
    "(temperatura, humedad, pH, conductividad eléctrica) y documentos científicos de respaldo. "
    "Tu tarea: identificar las 3 anomalías más críticas, explicar su causa probable, "
    "y proporcionar recomendaciones agronómicas accionables. "
    "Responde en español. Usa formato: RESUMEN EJECUTIVO: ... | ANOMALÍAS: 1) ... 2) ... 3) ... | "
    "RECOMENDACIONES: 1) ... Sé conciso y técnicamente preciso."
)


def _is_retriable(exc: BaseException) -> bool:
    status = getattr(exc, "status_code", None)
    return status in (429, 500, 502, 503, 504)


class NvidiaReportClient:
    """Synchronous NVIDIA NIM client (used inside Celery task)."""

    def __init__(self):
        self.model = settings.nvidia_report_model
        self._client = None

    @property
    def client(self):
        if self._client is None and settings.nvidia_api_key:
            self._client = OpenAI(
                api_key=settings.nvidia_api_key,
                base_url=settings.nvidia_base_url,
                timeout=120.0,
                max_retries=3,
            )
        return self._client

    @client.setter
    def client(self, value):
        self._client = value

    @classmethod
    def from_env(cls) -> "NvidiaReportClient":
        return cls()

    def _build_user_message(self, logs: List[dict], docs: List[dict]) -> str:
        telemetry = "\n".join(
            f"- {r.get('timestamp', '?')} | {r.get('sensor', '?')} | {r.get('value', '?')}"
            for r in (logs or [])[:60]
        )
        documents = "\n".join(
            f"- [{d.get('meta', {}).get('source', d.get('source', f'doc_{i}'))}]: "
            f"{(d.get('text') or '').strip().replace(chr(10), ' ')[:400]}"
            for i, d in enumerate(docs or [])
        )
        return (
            f"TELEMETRÍA DEL CAMPO:\n{telemetry or 'Sin datos de sensores.'}\n\n"
            f"DOCUMENTOS CIENTÍFICOS DE REFERENCIA:\n{documents or 'Sin documentos disponibles.'}\n\n"
            "Genera el reporte agrónomico completo."
        )

    @retry(
        retry=retry_if_exception(_is_retriable),
        wait=wait_exponential(multiplier=1.5, min=2, max=15),
        stop=stop_after_attempt(3),
        reraise=True,
    )
    def synthesize_insights(self, docs: List[dict], logs: List[dict]) -> Dict:
        """
        Calls NVIDIA NIM synchronously (Celery context).
        Returns dict with 'summary' and 'text' keys.
        """
        if not self.client:
            return {
                "summary": "Sin API Key configurada.",
                "text": "No se pudo generar el análisis de IA.",
            }

        user_message = self._build_user_message(logs, docs)
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": _SYSTEM_PROMPT},
                    {"role": "user", "content": user_message},
                ],
                temperature=0.2,
                max_tokens=1500,
                top_p=0.7,
            )
            text = response.choices[0].message.content or ""
            summary = text.split("|")[0].replace("RESUMEN EJECUTIVO:", "").strip()
            return {"summary": summary, "text": text}
        except Exception as e:
            logger.error(f"[NvidiaReportClient] LLM error: {e}", exc_info=True)
            return {"summary": "Error en síntesis IA.", "text": str(e)}
