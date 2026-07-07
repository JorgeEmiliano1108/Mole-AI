import os
from typing import Optional, List, Dict, Any
from openai import AsyncOpenAI
import yaml

from app.domain.schemas import ChatResponse, COFEPRIS_DISCLAIMER
from app.core.logger import logger
from app.core.config import settings
from app.core.circuit_breaker import AsyncCircuitBreaker, CircuitBreakerOpenError

class LLMClient:
    """Cliente LLM único con circuit‑breaker y fallback.

    Se basa en la API OpenAI‑compatible de NVIDIA NIM.
    """

    def __init__(self, model_name: Optional[str] = None, client: Optional[AsyncOpenAI] = None):
        self.api_key = settings.NVIDIA_API_KEY
        if not self.api_key:
            logger.warning("NVIDIA_API_KEY not detected – inference will fail.")
        self.base_url = settings.NVIDIA_BASE_URL
        self.model_name = model_name or settings.NVIDIA_CHAT_MODEL
        # Use provided client for testing or fallback to real client if credentials available
        if client is not None:
            self.client = client
        elif self.api_key:
            self.client = AsyncOpenAI(
                api_key=self.api_key,
                base_url=self.base_url,
                timeout=settings.LLM_TIMEOUT,
                max_retries=settings.LLM_MAX_RETRIES,
            )
        else:
            self.client = None  # No credentials; client actions will be mocked in tests
        self.breaker = AsyncCircuitBreaker(name="nvidia_llm", fail_max=settings.CB_FAIL_MAX, reset_timeout=settings.CB_RESET_TIMEOUT)

        # Load configurable disclaimer (versioned) from YAML
        disclaimer_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "prompts", "disclaimer.yaml"))
        try:
            with open(disclaimer_path, "r") as f:
                self.disclaimer = yaml.safe_load(f).get("disclaimer", COFEPRIS_DISCLAIMER)
        except Exception:
            self.disclaimer = COFEPRIS_DISCLAIMER

    async def _raw_generate(self, messages: List[Dict[str, Any]]) -> str:
        """Llamada directa a la API – sin circuit‑breaker.
        """
        if not self.client:
            raise RuntimeError("OpenAI client not configured – missing API key.")
        response = await self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            temperature=settings.LLM_TEMPERATURE,
            max_tokens=settings.LLM_MAX_TOKENS,
            top_p=settings.LLM_TOP_P,
        )
        return response.choices[0].message.content or ""

    async def generate(self, system_prompt: str, user_message: str) -> ChatResponse:
        """Genera la respuesta del LLM respetando el circuit‑breaker.
        En caso de *CircuitBreakerOpenError* se devuelve un fallback amigable.
        """
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]
        try:
            text = await self.breaker.call(lambda: self._raw_generate(messages))
            text = text.strip() or "Lo siento, no pude procesar esa solicitud correctamente."
            return ChatResponse(respuesta=text, disclaimer=COFEPRIS_DISCLAIMER)
        except CircuitBreakerOpenError:
            # Fallback cuando el breaker está abierto
            logger.error("LLM service unavailable – circuit breaker open")
            return ChatResponse(
                respuesta="El servidor de Inteligencia Artificial está en congestión. Intenta en unos minutos.",
                sources=[],
                disclaimer=COFEPRIS_DISCLAIMER,
            )
        except Exception as e:
            # Cualquier otro error – se propaga como fallback genérico
            logger.error("Error al invocar LLM: %s", e, exc_info=True)
            return ChatResponse(
                respuesta="El servidor de Inteligencia Artificial está en congestión. Intenta en unos minutos.",
                sources=[],
                disclaimer=COFEPRIS_DISCLAIMER,
            )
