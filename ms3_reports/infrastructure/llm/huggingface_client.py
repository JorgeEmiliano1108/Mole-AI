import os
import time
import httpx
from typing import List, Dict


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

    def synthesize_insights(self, docs: List[dict], logs: List[dict]) -> Dict:
        prompt = self._build_prompt(logs, docs)
        if not self.api_key:
            # fallback to deterministic stub
            return {"summary": "(stub) Resumen no disponible - HF key missing.", "text": "(stub) No se generaron recomendaciones."}

        url = f"https://api-inference.huggingface.co/models/{self.model}"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        payload = {"inputs": prompt, "parameters": {"max_new_tokens": 512}}

        # simple retry
        for attempt in range(3):
            try:
                resp = self._client.post(url, headers=headers, json=payload)
                if resp.status_code == 200:
                    # HF may return a JSON or plain text depending on model
                    try:
                        j = resp.json()
                        if isinstance(j, dict) and "generated_text" in j:
                            text = j["generated_text"]
                        elif isinstance(j, list) and len(j) > 0 and isinstance(j[0], dict) and "generated_text" in j[0]:
                            text = j[0]["generated_text"]
                        else:
                            text = resp.text
                    except Exception:
                        text = resp.text
                    return {"summary": text.splitlines()[0] if text else "", "text": text}
                else:
                    # transient
                    time.sleep(1 + attempt)
            except httpx.RequestError:
                time.sleep(1 + attempt)
                continue

        return {"summary": "(error) LLM unreachable", "text": "The HuggingFace model did not respond."}

