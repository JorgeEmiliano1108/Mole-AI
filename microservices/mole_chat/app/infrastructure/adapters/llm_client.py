import logging
import os
import asyncio
from typing import Any, Optional

from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.exceptions import OutputParserException
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception
from pydantic import ValidationError

from app.domain.schemas import ChatResponse

logger = logging.getLogger("ms2.llm_client")

# --- AVISO LEGAL INELUDIBLE (COFEPRIS / LEY GENERAL DE SALUD) ---
LEGAL_DISCLAIMER = (
    "\n\n---\n"
    "AVISO LEGAL: Mole.AI es una herramienta de asistencia agronómica "
    "basada en Inteligencia Artificial. La información proporcionada es "
    "estrictamente de carácter orientativo y no sustituye el diagnóstico, "
    "prescripción o tratamiento emitido por un Ingeniero Agrónomo o "
    "profesional certificado."
)

def _should_retry_exception(exc: BaseException) -> bool:
    if isinstance(exc, (asyncio.TimeoutError, ConnectionError, TimeoutError)):
        return True
    
    status = getattr(exc, "status_code", None)
    if status in (429, 500, 502, 503, 504):
        return True
        
    msg = str(exc).lower()
    return any(x in msg for x in ["429", "500", "502", "503", "504", "timeout", "rate limit", "overloaded"])

class LLMClient:
    def __init__(self, model_name: Optional[str] = None, max_retries: int = 3):
        self.model_name = model_name or os.getenv("LLM_MODEL_ID", "deepseek-ai/DeepSeek-R1-Distill-Qwen-7B")
        self.api_key = os.getenv("HUGGINGFACE_API_KEY")
        self.base_url = os.getenv("HF_INFERENCE_API_URL", "https://router.huggingface.co/hf-inference/v1")
        
        # Use settings for timeout
        from app.core.config import settings
        
        self.llm = ChatOpenAI(
            model=self.model_name,
            api_key=self.api_key,
            base_url=self.base_url,
            max_retries=0,
            timeout=settings.LLM_REQUEST_TIMEOUT,
            max_tokens=settings.LLM_MAX_NEW_TOKENS
        )
        
        self.parser = PydanticOutputParser(pydantic_object=ChatResponse)
        self.max_retries = max_retries

    @retry(
        retry=retry_if_exception(_should_retry_exception), 
        wait=wait_exponential(multiplier=1.5, min=2, max=15),
        stop=stop_after_attempt(3), 
        reraise=True
    )
    async def _call_llm(self, prompt_text: str) -> ChatResponse:
        format_instructions = self.parser.get_format_instructions()
        final_prompt = f"{prompt_text}\n\nINSTRUCCIONES DE FORMATO OBLIGATORIAS:\n{format_instructions}"
        
        logger.info(f"Iniciando inferencia RAG con LLM ({self.model_name})...")
        chain = self.llm | self.parser
        return await chain.ainvoke(final_prompt)

    async def generate(self, prompt_text: str) -> ChatResponse:
        try:
            validated_response: ChatResponse = await self._call_llm(prompt_text)
            
            # [RF-AI-ETH-001] Inyección Obligatoria del Disclaimer
            validated_response.disclaimer = LEGAL_DISCLAIMER
            
            return validated_response
            
        except (ValidationError, OutputParserException) as parse_err:
            logger.error(f"[LLMClient] Error de parseo: {parse_err}")
            return self._fallback_response()
            
        except Exception as e:
            logger.warning(f"[LLMClient] Colapso tras agotar reintentos: {e}", exc_info=True)
            return self._fallback_response()
            
    def _fallback_response(self) -> ChatResponse:
        return ChatResponse(
            respuesta="El servidor de Inteligencia Artificial está experimentando congestión. Por favor, intenta de nuevo en unos minutos.",
            sources=[],
            disclaimer=LEGAL_DISCLAIMER
        )