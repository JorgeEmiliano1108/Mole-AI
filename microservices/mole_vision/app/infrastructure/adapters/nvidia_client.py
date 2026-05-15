import os
import logging
from typing import Optional, List, Dict, Any
from openai import AsyncOpenAI

logger = logging.getLogger(__name__)

class NvidiaBaseClient:
    """
    Cliente nativo asíncrono OpenAI-compatible para NVIDIA NIM.
    """
    def __init__(self, model_name: Optional[str] = None):
        self.api_key = os.getenv("NVIDIA_API_KEY")
        if not self.api_key:
            logger.warning("NVIDIA_API_KEY no detectado. Inferencia fallará.")
            
        self.base_url = os.getenv("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1")
        self.model_name = model_name or os.getenv("NVIDIA_CHAT_MODEL", "meta/llama-3.3-70b-instruct")
        
        self.client = AsyncOpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
            timeout=120.0,
            max_retries=3,
        )

    async def generate_chat(self, messages: List[Dict[str, Any]], temperature: float = 0.2, max_tokens: int = 1024) -> str:
        """
        Llamada genérica al endpoint de chat/completions.
        """
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
