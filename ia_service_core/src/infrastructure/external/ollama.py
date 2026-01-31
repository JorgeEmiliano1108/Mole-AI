import httpx
from typing import List
from src.application.ports.output import LLMService
from src.infrastructure.config.settings import settings

class OllamaAdapter(LLMService):
    """
    Implementación real que habla con el servidor de Ollama.
    """
    def __init__(self):
        self.base_url = settings.OLLAMA_BASE_URL
        self.model = settings.LLM_MODEL
        self.embed_model = settings.EMBEDDING_MODEL

    async def get_embedding(self, text: str) -> List[float]:
        """Consulta a Ollama para obtener el vector numérico del texto."""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.base_url}/api/embeddings",
                    json={"model": self.embed_model, "prompt": text},
                    timeout=10.0
                )
                response.raise_for_status()
                return response.json().get("embedding", [])
            except Exception as e:
                print(f"Error conectando con Ollama (Embedding): {e}")
                return []

    async def generate_response(self, prompt: str) -> str:
        """Pide a Ollama que complete el texto (Chat)."""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "stream": False,
                        "options": {"temperature": 0.3} # Menos creativo, más preciso
                    },
                    timeout=60.0 # Darle tiempo para pensar
                )
                response.raise_for_status()
                return response.json().get("response", "")
            except Exception as e:
                return f"Error generando respuesta: {str(e)}"