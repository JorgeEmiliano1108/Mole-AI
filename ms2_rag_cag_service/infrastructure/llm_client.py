import logging
import os
from typing import Any, Optional

from langchain_community.llms import ChatOpenAI
from langchain_core.output_parsers import PydanticOutputParser
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception
from pydantic import ValidationError

from ms2_rag_cag_service.domain.models import ChatResponse


def _should_retry_exception(exc: Exception) -> bool:
    """Return True if exception indicates a retryable HTTP error (429,500,502,504).
    Looks for `status_code` attribute or common message substrings.
    """
    # Check attribute
    status = getattr(exc, "status_code", None)
    if status in (429, 500, 502, 504):
        return True
    # Check message
    msg = str(exc)
    for code in ("429", "500", "502", "504"):
        if code in msg:
            return True
    return False


class LLMClient:
    def __init__(self, model_name: Optional[str] = None, max_retries: int = 3):
        model_name = model_name or os.getenv("MODEL_NAME", "gpt-3.5-turbo")
        self.llm = ChatOpenAI(model=model_name)
        self.parser = PydanticOutputParser(pydantic_object=ChatResponse)
        self.max_retries = max_retries

    @retry(retry=retry_if_exception(_should_retry_exception), wait=wait_exponential(multiplier=1, min=1, max=10), stop=stop_after_attempt(3), reraise=True)
    async def _call_llm(self, prompt_text: str) -> Any:
        # direct pass-through to langchain llm async invocation
        return await self.llm.ainvoke(prompt_text, output_parser=self.parser)

    async def generate(self, prompt_text: str) -> ChatResponse:
        try:
            raw = await self._call_llm(prompt_text)
            # raw should already be structured by the PydanticOutputParser but validate again
            try:
                validated = ChatResponse.model_validate(raw)
                return validated
            except ValidationError as ve:
                logging.error(f"[LLMClient] Validation error on LLM output: {ve}")
                # Fallback structured response
                return ChatResponse.model_validate({
                    "respuesta": "El servicio de análisis agronómico está experimentando alta demanda. Por favor, intenta de nuevo en unos minutos.",
                    "sources": [],
                    "disclaimer": ""
                })
        except Exception as e:
            # Final fallback after retries exhausted
            logging.warning(f"[LLMClient] LLM call failed after retries: {e}")
            return ChatResponse.model_validate({
                "respuesta": "El servicio de análisis agronómico está experimentando alta demanda. Por favor, intenta de nuevo en unos minutos.",
                "sources": [],
                "disclaimer": ""
            })
