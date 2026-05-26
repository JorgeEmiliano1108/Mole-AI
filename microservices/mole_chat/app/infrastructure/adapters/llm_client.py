"""
Infrastructure Layer - Adapter: LLM Client (NVIDIA NIM via openai)
Reemplaza: langchain_openai.ChatOpenAI + Ollama
"""
import logging
import os
from typing import Optional

from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception

from app.domain.schemas import ChatResponse, COFEPRIS_DISCLAIMER
from app.infrastructure.adapters.nvidia_client import NvidiaBaseClient

logger = logging.getLogger("ms2.llm_client")


def _should_retry(exc: BaseException) -> bool:
    status = getattr(exc, "status_code", None)
    if status in (429, 500, 502, 503, 504):
        return True
    msg = str(exc).lower()
    return any(x in msg for x in ["429", "timeout", "rate limit", "overloaded"])


class LLMClient:
    def __init__(self, model_name: Optional[str] = None):
        self.model_name = model_name or os.getenv("NVIDIA_CHAT_MODEL", "meta/llama-3.3-70b-instruct")
        self.nim = NvidiaBaseClient(model_name=self.model_name)

    @retry(
        retry=retry_if_exception(_should_retry),
        wait=wait_exponential(multiplier=1.5, min=2, max=15),
        stop=stop_after_attempt(3),
        reraise=True,
    )
    async def _call(self, messages: list) -> str:
        logger.info(f"Inferencia NVIDIA NIM ({self.model_name})")
        return await self.nim.generate_chat(messages, temperature=0.2, max_tokens=1024)

    async def generate(self, system_prompt: str, user_message: str) -> ChatResponse:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]
        try:
            text = await self._call(messages)
            text = text.strip() or "Lo siento, no pude procesar esa solicitud correctamente."
            return ChatResponse(respuesta=text, disclaimer=COFEPRIS_DISCLAIMER)

        except Exception as e:
            logger.warning(f"[LLMClient] Colapso tras reintentos: {e}", exc_info=True)
            return ChatResponse(
                respuesta="El servidor de Inteligencia Artificial está en congestión. Intenta en unos minutos.",
                sources=[],
                disclaimer=COFEPRIS_DISCLAIMER,
            )