import os
import httpx
from typing import List, Dict
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type


class HuggingFaceClient:
    def __init__(self, api_key: str | None = None, model: str | None = None):
        self.api_key = api_key or os.getenv("MS3_HF_KEY")
        self.model = model or os.getenv("MS3_HF_MODEL") or "google/flan-t5-large"
        self._client = httpx.Client(timeout=60.0)

    @classmethod
    def from_env(cls):
        return cls(os.getenv("MS3_HF_KEY"), os.getenv("MS3_HF_MODEL"))

    def _build_prompt(self, logs: List[dict], docs: List[dict]) -> str:
        # Structured prompt: role, tasks, data sections, output format
        header = (
            "You are an expert Agronomist Engineer. Cross telemetry sensor data with the provided"
            " botanical/scientific documents and provide clear actionable insights. For each insight,"
            " include a citation referencing the document id or source. Use formal tone and be concise.\n\n"
        )

        telemetry_section = "TELEMETRY:\n"
        for row in (logs or [])[:50]:
            telemetry_section += f"- {row.get('timestamp')} | {row.get('sensor')} | {row.get('value')}\n"

        docs_section = "DOCUMENTS (id: text snippet):\n"
        for i, d in enumerate(docs or []):
            source = d.get("meta", {}).get("source") or d.get("source") or f"doc_{i}"
            snippet = (d.get("text") or "").strip().replace("\n", " ")[:400]
            docs_section += f"- {source}: {snippet}\n"

        task = (
            "Tasks:\n"
            "1) Identify top 3 actionable insights linking telemetry anomalies to botanical knowledge.\n"
            "2) For each insight, provide a short rationale (1-2 sentences) and a citation in the format [SOURCE].\n"
            "3) Provide a short executive summary (max 3 sentences).\n"
        )

        output = "Output format:\nSUMMARY:\n- <one-line summary>\nINSIGHTS:\n- Insight 1:\n  rationale: ...\n  citation: [SOURCE]\n- Insight 2: ...\n"

        prompt = header + telemetry_section + "\n" + docs_section + "\n" + task + "\n" + output
        return prompt

    @retry(
        retry=retry_if_exception_type((httpx.RequestError, httpx.HTTPStatusError)),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        stop=stop_after_attempt(3),
        reraise=True,
    )
    def _call_hf_api(self, url: str, headers: dict, payload: dict) -> str:
        """Make a single HuggingFace API call with tenacity retry (M5)."""
        resp = self._client.post(url, headers=headers, json=payload)
        resp.raise_for_status()
        try:
            j = resp.json()
            if isinstance(j, dict) and "generated_text" in j:
                return j["generated_text"]
            elif isinstance(j, list) and len(j) > 0 and isinstance(j[0], dict) and "generated_text" in j[0]:
                return j[0]["generated_text"]
            else:
                return resp.text
        except Exception:
            return resp.text

    def synthesize_insights(self, docs: List[dict], logs: List[dict]) -> Dict:
        prompt = self._build_prompt(logs, docs)
        if not self.api_key:
            # fallback to deterministic stub
            return {"summary": "(stub) Resumen no disponible - HF key missing.", "text": "(stub) No se generaron recomendaciones."}

        url = f"https://api-inference.huggingface.co/models/{self.model}"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        payload = {"inputs": prompt, "parameters": {"max_new_tokens": 512}}

        try:
            text = self._call_hf_api(url, headers, payload)
            return {"summary": text.splitlines()[0] if text else "", "text": text}
        except Exception:
            return {"summary": "(error) LLM unreachable", "text": "The HuggingFace model did not respond."}


