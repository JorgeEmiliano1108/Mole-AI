import os
import logging
import base64
import io
import json
import asyncio
from typing import Dict, Any, Optional
from PIL import Image
import torch
import requests
from transformers import AutoTokenizer, AutoProcessor, Phi3ForCausalLM

from ...domain.ports import VisionProviderPort, ModelManagementPort
from ...domain.models.plant import VisualAnalysis, PlantImage, PlantState
from ...domain.exceptions import (
    VisionAnalysisError, 
    ModelNotReadyError, 
    InvalidImageError,
    ServiceUnavailableError
)

logger = logging.getLogger(__name__)


class Phi3VisionAdapter(VisionProviderPort, ModelManagementPort):
    """Adaptador unificado para Phi-3.5 Vision-Instruct Q4"""
    
    def __init__(self):
        self.model = None
        self.processor = None
        self.tokenizer = None
        self.device = "cpu"
        self.model_name = os.getenv("MODEL_NAME", "microsoft/Phi-3.5-vision-instruct")
        self.use_local_ollama = os.getenv("USE_LOCAL_OLLAMA", "false").lower() == "true"
        self.ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
        self._model_ready = False
        
    async def initialize(self):
        """Inicializa el adaptador Phi-3.5"""
        try:
            logger.info(f"Inicializando Phi-3.5 Vision-Instruct: {self.model_name}")
            
            if self.use_local_ollama:
                await self._setup_ollama()
            else:
                await self._setup_transformers()
                
            self._model_ready = True
            logger.info("✅ Phi-3.5 Vision-Instruct inicializado correctamente")
            
        except Exception as e:
            logger.error(f"❌ Error inicializando Phi-3.5: {str(e)}")
            raise VisionAnalysisError(f"No se pudo inicializar el modelo: {str(e)}")

    async def _setup_transformers(self):
        """Configura modelo usando Transformers local"""
        try:
            self.model = Phi3ForCausalLM.from_pretrained(
                self.model_name,
                device_map="cpu",
                torch_dtype=torch.float16,
                trust_remote_code=True,
                _attn_implementation='eager'
            )
            
            self.processor = AutoProcessor.from_pretrained(
                self.model_name,
                trust_remote_code=True
            )
            
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_name,
                trust_remote_code=True
            )
            
            logger.info("✅ Modelo Phi-3.5 cargado con transformers")
            
        except Exception as e:
            logger.error(f"Error cargando modelo con transformers: {str(e)}")
            raise VisionAnalysisError(f"Error cargando modelo: {str(e)}")

    async def _setup_ollama(self):
        """Configura conexión con Ollama"""
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=10)
            if response.status_code == 200:
                models = response.json().get("models", [])
                phi_models = [m for m in models if "phi" in m.get("name", "").lower()]
                
                if phi_models:
                    logger.info(f"✅ Phi-3.5 encontrado en Ollama: {phi_models[0]['name']}")
                else:
                    logger.warning("Phi-3.5 no encontrado en Ollama, intentando descargar...")
                    await self._pull_ollama_model()
            else:
                raise ServiceUnavailableError("Ollama service not available")
                
        except Exception as e:
            logger.error(f"Error configurando Ollama: {str(e)}")
            raise ServiceUnavailableError(f"Error Ollama: {str(e)}")

    async def _pull_ollama_model(self):
        """Descarga modelo Phi-3.5 desde Ollama"""
        try:
            logger.info("Descargando Phi-3.5 desde Ollama...")
            response = requests.post(
                f"{self.ollama_url}/api/pull",
                json={"name": "phi3.5:latest"},
                timeout=300
            )
            if response.status_code == 200:
                logger.info("✅ Phi-3.5 descargado correctamente")
            else:
                raise ServiceUnavailableError("Error descargando modelo")
        except Exception as e:
            logger.error(f"Error descargando modelo: {str(e)}")
            raise ServiceUnavailableError(f"Error descarga: {str(e)}")

    async def analyze_plant_image(
        self, 
        image: PlantImage, 
        context: Optional[str] = None
    ) -> Dict[str, Any]:
        """Analiza imagen de planta usando Phi-3.5"""
        try:
            if not await self.is_model_ready():
                raise ModelNotReadyError("Modelo no listo para inferencia")
            
            decoded_image = self._decode_image(image.image_base64)
            
            if self.use_local_ollama:
                return await self._analyze_with_ollama(decoded_image, context)
            else:
                return await self._analyze_with_transformers(decoded_image, context)
                
        except Exception as e:
            logger.error(f"Error en análisis visual: {str(e)}")
            raise VisionAnalysisError(f"Error análisis imagen: {str(e)}")

    def _decode_image(self, base64_str: str) -> Image.Image:
        """Decodifica imagen base64"""
        try:
            image_data = base64.b64decode(base64_str)
            image = Image.open(io.BytesIO(image_data))
            return image.convert("RGB")
        except Exception as e:
            logger.error(f"Error decodificando imagen: {str(e)}")
            raise InvalidImageError("Formato de imagen inválido")

    async def _analyze_with_transformers(
        self, 
        image: Image.Image, 
        context: Optional[str] = None
    ) -> Dict[str, Any]:
        """Analiza imagen usando Transformers local"""
        try:
            prompt = self._create_vision_prompt(context)
            
            image_buffer = io.BytesIO()
            image.save(image_buffer, format='JPEG')
            image_bytes = image_buffer.getvalue()
            image_base64 = base64.b64encode(image_bytes).decode()
            
            messages = [
                {"role": "user", "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}}
                ]}
            ]
            
            text = self.processor.tokenizer.apply_chat_template(
                messages, 
                tokenize=False, 
                add_generation_prompt=True
            )
            
            image_inputs = self.processor.image_processor(
                images=[image], 
                return_tensors="pt"
            )
            
            text_inputs = self.processor.tokenizer(
                text, 
                return_tensors="pt", 
                add_special_tokens=False
            )
            
            inputs = {
                **image_inputs,
                **text_inputs
            }
            
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=512,
                    do_sample=True,
                    temperature=0.2,
                    pad_token_id=self.tokenizer.eos_token_id
                )
            
            response_text = self.processor.tokenizer.decode(
                outputs[0][text_inputs['input_ids'].shape[1]:], 
                skip_special_tokens=True
            )
            
            return self._parse_vision_response(response_text)
            
        except Exception as e:
            logger.error(f"Error análisis con transformers: {str(e)}")
            raise VisionAnalysisError(f"Error transformers: {str(e)}")

    async def _analyze_with_ollama(
        self, 
        image: Image.Image, 
        context: Optional[str] = None
    ) -> Dict[str, Any]:
        """Analiza imagen usando Ollama"""
        try:
            prompt = self._create_vision_prompt(context)
            
            image_buffer = io.BytesIO()
            image.save(image_buffer, format='JPEG')
            image_bytes = image_buffer.getvalue()
            
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": "phi3.5:latest",
                    "prompt": prompt,
                    "images": [base64.b64encode(image_bytes).decode()],
                    "stream": False,
                    "options": {
                        "temperature": 0.2,
                        "top_p": 0.9,
                        "max_tokens": 512
                    }
                },
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                response_text = result.get("response", "")
                return self._parse_vision_response(response_text)
            else:
                raise ServiceUnavailableError(f"Ollama error: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Error análisis con Ollama: {str(e)}")
            raise ServiceUnavailableError(f"Error Ollama: {str(e)}")

    def _create_vision_prompt(self, context: Optional[str] = None) -> str:
        """Crea prompt para análisis visual"""
        base_prompt = """Eres un experto agrónomo especializado en análisis visual de plantas.

Analiza la imagen proporcionada y determina:

RESPUESTA OBLIGATORIA (JSON exacto):
{
    "estado": "Sana|Atención|Peligro",
    "confianza": 0.0-1.0,
    "especie_probable": "nombre_científico o 'Desconocida'",
    "sintomas_visibles": ["síntoma1", "síntoma2"],
    "areas_afectadas": ["área1", "área2"],
    "severidad_visual": 0.0-1.0,
    "análisis_visual": "descripción detallada del análisis visual"
}

ANÁLISIS VISUAL:"""

        if context:
            base_prompt += f"\n\nCONTEXTO ADICIONAL:\n{context}\n\n"
        
        return base_prompt

    def _parse_vision_response(self, response_text: str) -> Dict[str, Any]:
        """Parsea respuesta del modelo a formato estructurado"""
        try:
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            
            if json_start != -1 and json_end > json_start:
                json_str = response_text[json_start:json_end]
                parsed = json.loads(json_str)
                
                required_fields = ["estado", "confianza", "análisis_visual"]
                for field in required_fields:
                    if field not in parsed:
                        parsed[field] = self._get_default_vision_value(field)
                
                parsed.setdefault("especie_probable", "Desconocida")
                parsed.setdefault("sintomas_visibles", [])
                parsed.setdefault("areas_afectadas", [])
                parsed.setdefault("severidad_visual", 0.5)
                
                return parsed
            else:
                logger.warning("No se encontró JSON válido en respuesta visual")
                return self._create_fallback_visual_analysis()
                
        except json.JSONDecodeError as e:
            logger.error(f"Error parseando respuesta visual: {str(e)}")
            return self._create_fallback_visual_analysis()

    def _get_default_vision_value(self, field: str) -> Any:
        """Retorna valor por defecto para campo visual"""
        defaults = {
            "estado": "Atención",
            "confianza": 0.5,
            "especie_probable": "Desconocida",
            "sintomas_visibles": [],
            "areas_afectadas": [],
            "severidad_visual": 0.5,
            "análisis_visual": "Análisis visual limitado - requiere revisión manual"
        }
        return defaults.get(field, None)

    def _create_fallback_visual_analysis(self) -> Dict[str, Any]:
        """Crea análisis visual de respaldo"""
        return {
            "estado": "Atención",
            "confianza": 0.3,
            "especie_probable": "Desconocida",
            "sintomas_visibles": ["análisis limitado"],
            "areas_afectadas": ["indeterminado"],
            "severidad_visual": 0.5,
            "análisis_visual": "Sistema temporalmente limitado - se recomienda revisión manual"
        }

    # Métodos de ModelManagementPort
    async def load_model(self, model_name: str) -> bool:
        """Carga modelo específico"""
        try:
            self.model_name = model_name
            await self.initialize()
            return True
        except Exception as e:
            logger.error(f"Error cargando modelo {model_name}: {str(e)}")
            return False

    async def is_model_ready(self) -> bool:
        """Verifica si modelo está listo"""
        try:
            if self.use_local_ollama:
                response = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
                if response.status_code == 200:
                    models = response.json().get("models", [])
                    return any("phi" in m.get("name", "").lower() for m in models)
                return False
            else:
                return self.model is not None and self.processor is not None
        except:
            return False

    async def get_model_info(self) -> Dict[str, Any]:
        """Obtiene información del modelo"""
        return {
            "model_name": self.model_name,
            "implementation": "ollama" if self.use_local_ollama else "transformers",
            "device": self.device,
            "ready": self._model_ready,
            "supports_vision": True,
            "supports_text": True,
            "multimodal": True
        }