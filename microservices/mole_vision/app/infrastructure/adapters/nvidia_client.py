import logging
from typing import Optional, List, Dict, Any
from openai import AsyncOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception
from app.core.config import settings

logger = logging.getLogger(__name__)


def _is_nvidia_retriable(exc: BaseException) -> bool:
    """Retry on rate limits and server errors; fail fast on auth/bad request."""
    status = getattr(exc, "status_code", None)
    return status in (429, 500, 502, 503, 504)


class NvidiaBaseClient:
    """
    Cliente nativo asíncrono OpenAI-compatible para NVIDIA NIM.
    """
    def __init__(self, model_name: Optional[str] = None):
        self.api_key = settings.NVIDIA_API_KEY
        if not self.api_key:
            logger.warning("NVIDIA_API_KEY no detectado. Inferencia fallará.")

        self.base_url = settings.NVIDIA_BASE_URL
        self.model_name = model_name or settings.NVIDIA_CHAT_MODEL

        self._client: Optional[AsyncOpenAI] = None

    @property
    def client(self) -> Optional[AsyncOpenAI]:
        if self._client is None and self.api_key:
            self._client = AsyncOpenAI(
                api_key=self.api_key,
                base_url=self.base_url,
                timeout=120.0,
                max_retries=3,
            )
        return self._client

    @retry(
        retry=retry_if_exception(_is_nvidia_retriable),
        wait=wait_exponential(multiplier=1.5, min=2, max=15),
        stop=stop_after_attempt(3),
        reraise=True,
    )
    async def generate_chat(self, messages: List[Dict[str, Any]], temperature: float = 0.2, max_tokens: int = 1024) -> str:
        """
        Llamada genérica al endpoint de chat/completions.
        """
        if not self.client:
            return "Sin API Key configurada."
        try:
            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=0.7,
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            logger.error(f"Fallo en inferencia NVIDIA NIM: {e}", exc_info=True)
            raise

    async def generate_vision(self, prompt: str, image_b64: str, max_tokens: int = 1024) -> str:
        """
        Llamada especializada para modelos multimodales (ej. llama-3.2-11b-vision-instruct).
        """
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{image_b64}"
                        }
                    }
                ]
            }
        ]
        return await self.generate_chat(messages, temperature=0.1, max_tokens=max_tokens)
