import logging
import os
import asyncio
from typing import Any, Optional

from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.exceptions import OutputParserException
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception
from pydantic import ValidationError

from ms2_rag_cag_service.domain.models import ChatResponse

logger = logging.getLogger("ms2.llm_client")

def _should_retry_exception(exc: BaseException) -> bool:
    """Determina si la excepción es recuperable (Timeouts o Errores de Servidor)."""
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
        self.api_key = os.getenv("HUGGINGFACE_API_KEY", "dummy_key")
        
        # FIX: Actualización estricta al nuevo router de Hugging Face
        self.base_url = os.getenv("HF_INFERENCE_API_URL", "https://router.huggingface.co/hf-inference/v1")
        
        self.llm = ChatOpenAI(
            model=self.model_name,
            api_key=self.api_key,
            base_url=self.base_url,
            max_retries=0,
            timeout=int(os.getenv("HF_API_TIMEOUT", "30"))
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
            return validated_response
            
        except (ValidationError, OutputParserException) as parse_err:
            logger.error(f"[LLMClient] Error de parseo (Alucinación de formato): {parse_err}")
            return self._fallback_response()
            
        except Exception as e:
            logger.warning(f"[LLMClient] Colapso definitivo tras agotar reintentos: {e}", exc_info=True)
            return self._fallback_response()
            
    def _fallback_response(self) -> ChatResponse:
        """Respuesta defensiva instanciando exactamente los campos de tu modelo."""
        return ChatResponse(
            respuesta="El servidor de Inteligencia Artificial está experimentando congestión de red debido a alta demanda. Por favor, intenta de nuevo en unos minutos.",
            sources=[],
            disclaimer="AVISO LEGAL: Modo de contingencia activo por latencia de red. La información proporcionada es estrictamente informativa."
        )