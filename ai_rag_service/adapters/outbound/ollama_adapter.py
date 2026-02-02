import httpx
import time
from typing import List, Dict, Any, Optional

from ..ports.input import LLMProviderPort
from ..domain.models import LLMResponse
from ..domain.exceptions import LLMServiceError, EmbeddingGenerationError
from ..config.settings import settings

class OllamaAdapter(LLMProviderPort):
    """Adaptador optimizado para Ollama con configuración específica de Mole AI"""
    
    def __init__(self):
        self.base_url = settings.OLLAMA_BASE_URL
        self.model = settings.LLM_MODEL
        self.embed_model = settings.EMBEDDING_MODEL
        
        # Configuración crítica para Mole AI
        self.temperature = settings.LLM_TEMPERATURE  # 0.2 - baja creatividad
        self.context_window = settings.LLM_CONTEXT_WINDOW  # 4096
        self.max_tokens = settings.LLM_MAX_TOKENS
        
        # System prompt fijo para Mole AI
        self.system_prompt = settings.MOLE_AI_SYSTEM_PROMPT
    
    async def generate_response(
        self, 
        prompt: str, 
        system_prompt: Optional[str] = None,
        context: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Genera respuesta con configuración específica de Mole AI"""
        start_time = time.time()
        
        try:
            # Construir prompt con contexto RAG
            full_prompt = self._build_contextual_prompt(prompt, context)
            
            # Usar system prompt de Mole AI o el proporcionado
            final_system_prompt = system_prompt or self.system_prompt
            
            # Configuración específica para respuestas precisas
            payload = {
                "model": self.model,
                "prompt": full_prompt,
                "system": final_system_prompt,
                "stream": False,
                "options": {
                    "temperature": self.temperature,  # 0.2 - mínimo de creatividad
                    "top_p": 0.9,
                    "top_k": 20,
                    "repeat_penalty": 1.1,
                    "num_ctx": self.context_window,
                    "num_predict": self.max_tokens,
                    "stop": ["</response>", "Human:", "Usuario:"]  # Prevener alucinaciones
                }
            }
            
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )
                response.raise_for_status()
                
                result = response.json()
                processing_time = time.time() - start_time
                
                # Calcular tokens usados (estimación)
                tokens_used = len(full_prompt.split()) + len(result.get("response", "").split())
                
                return LLMResponse(
                    content=result.get("response", ""),
                    model_used=self.model,
                    tokens_used=tokens_used,
                    processing_time=processing_time,
                    success=True,
                    context_used=context or []
                ).to_dict()
                
        except httpx.TimeoutException:
            raise LLMServiceError("Timeout en la respuesta de Ollama")
        except httpx.HTTPStatusError as e:
            raise LLMServiceError(f"Error HTTP de Ollama: {e.response.status_code}")
        except Exception as e:
            raise LLMServiceError(f"Error generando respuesta: {str(e)}")
    
    async def get_embedding(self, text: str) -> List[float]:
        """Genera embedding para texto con modelo específico"""
        try:
            payload = {
                "model": self.embed_model,
                "prompt": text,
                "options": {
                    "temperature": 0.0  # Determinista para embeddings
                }
            }
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.base_url}/api/embeddings",
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )
                response.raise_for_status()
                
                result = response.json()
                embedding = result.get("embedding", [])
                
                if not embedding:
                    raise EmbeddingGenerationError("Embedding vacío recibido")
                
                return embedding
                
        except httpx.HTTPStatusError as e:
            raise EmbeddingGenerationError(f"Error HTTP en embedding: {e.response.status_code}")
        except Exception as e:
            raise EmbeddingGenerationError(f"Error generando embedding: {str(e)}")
    
    def _build_contextual_prompt(self, prompt: str, context: Optional[List[str]]) -> str:
        """Construye prompt con contexto RAG"""
        if not context:
            return prompt
        
        context_text = "\n---\n".join([f"CONTEXTO {i+1}: {ctx}" for i, ctx in enumerate(context)])
        
        contextual_prompt = f"""
{context_text}

---

USANDO EXCLUSIVAMENTE EL CONTEXTO PROPORCIONADO, responde:
{prompt}

Si el contexto no contiene información suficiente, indica claramente: "No tengo suficiente información para responder completamente."
"""
        return contextual_prompt
    
    async def health_check(self) -> Dict[str, Any]:
        """Verifica disponibilidad del servicio Ollama"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                response.raise_for_status()
                
                models = response.json().get("models", [])
                available_models = [model["name"] for model in models]
                
                return {
                    "service_available": True,
                    "model_available": self.model in available_models,
                    "embedding_model_available": self.embed_model in available_models,
                    "available_models": available_models
                }
                
        except Exception as e:
            return {
                "service_available": False,
                "error": str(e),
                "model_available": False,
                "embedding_model_available": False,
                "available_models": []
            }
    
    async def list_models(self) -> List[str]:
        """Lista modelos disponibles en Ollama"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                response.raise_for_status()
                
                models = response.json().get("models", [])
                return [model["name"] for model in models]
                
        except Exception as e:
            raise LLMServiceError(f"Error listando modelos: {str(e)}")

class OllamaStreamAdapter(OllamaAdapter):
    """Adaptador con soporte de streaming para respuestas largas"""
    
    async def generate_response_stream(
        self, 
        prompt: str, 
        system_prompt: Optional[str] = None,
        context: Optional[List[str]] = None
    ):
        """Genera respuesta en streaming"""
        try:
            full_prompt = self._build_contextual_prompt(prompt, context)
            final_system_prompt = system_prompt or self.system_prompt
            
            payload = {
                "model": self.model,
                "prompt": full_prompt,
                "system": final_system_prompt,
                "stream": True,
                "options": {
                    "temperature": self.temperature,
                    "top_p": 0.9,
                    "top_k": 20,
                    "num_ctx": self.context_window,
                    "num_predict": self.max_tokens
                }
            }
            
            async with httpx.AsyncClient(timeout=120.0) as client:
                async with client.stream(
                    "POST",
                    f"{self.base_url}/api/generate",
                    json=payload,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    response.raise_for_status()
                    
                    async for line in response.aiter_lines():
                        if line.strip():
                            try:
                                data = eval(line)  # Ollama envía JSON por línea
                                yield data.get("response", "")
                            except:
                                continue
                                
        except Exception as e:
            raise LLMServiceError(f"Error en streaming: {str(e)}")