"""Adapter Outbound: Phi-3.5 Vision Model Integration"""

import logging
import base64
import json
import asyncio
from typing import Optional
from io import BytesIO

import torch
from transformers import AutoModelForCausalLM, AutoProcessor
from PIL import Image

from ...domain.models import VisionAnalysisRequest, VisionAnalysisResult, PlantState, PlantSymptom
from ...domain.ports import VisionModelPort
from ...domain.exceptions import InvalidImageException, AnalysisFailedException

logger = logging.getLogger(__name__)


class Phi3VisionAdapter(VisionModelPort):
    """Implementación de VisionModelPort usando Phi-3.5 Vision-Instruct Q4"""
    
    def __init__(self, model_name: str = "microsoft/Phi-3.5-vision-instruct"):
        self.model_name = model_name
        self.model = None
        self.processor = None
        self.device = "cpu"  # Q4 optimizado para CPU
        self._initialized = False
        logger.info(f"Phi3VisionAdapter inicializado (modelo será cargado en initialize())")
    
    async def initialize(self):
        """Carga modelo Phi-3.5 de forma asíncrona"""
        try:
            logger.info(f"⏳ Cargando {self.model_name}...")
            
            # Cargar processor
            self.processor = await asyncio.to_thread(
                AutoProcessor.from_pretrained,
                self.model_name,
                trust_remote_code=True
            )
            
            # Cargar modelo con Q4
            self.model = await asyncio.to_thread(
                AutoModelForCausalLM.from_pretrained,
                self.model_name,
                device_map=self.device,
                trust_remote_code=True,
                torch_dtype=torch.float16,
            )
            
            self.model.eval()
            self._initialized = True
            logger.info(f"✅ Phi-3.5 cargado exitosamente")
            
        except Exception as e:
            logger.error(f"❌ Error cargando Phi-3.5: {str(e)}")
            raise
    
    async def is_ready(self) -> bool:
        """Verifica si el modelo está inicializado"""
        return self._initialized and self.model is not None
    
    async def analyze_image(self, request: VisionAnalysisRequest) -> VisionAnalysisResult:
        """
        Analiza imagen con Phi-3.5 Vision
        
        Args:
            request: VisionAnalysisRequest con imagen base64
            
        Returns:
            VisionAnalysisResult estructurado
        """
        try:
            # Decodificar imagen
            image_data = base64.b64decode(request.image_base64)
            image = Image.open(BytesIO(image_data)).convert("RGB")
            logger.info(f"✅ Imagen decodificada: {image.size}")
            
            # Crear prompt
            prompt = self._create_vision_prompt()
            
            # Procesar inputs
            inputs = await asyncio.to_thread(
                self.processor,
                text=prompt,
                images=[image],
                return_tensors="pt"
            )
            
            # Mover a device
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            # Inferencia
            logger.info("🧠 Ejecutando inferencia...")
            with torch.no_grad():
                outputs = await asyncio.to_thread(
                    self.model.generate,
                    **inputs,
                    max_new_tokens=512,
                    temperature=0.7,
                    do_sample=False
                )
            
            # Decodificar
            response_text = self.processor.decode(outputs[0], skip_special_tokens=True)
            logger.info(f"📝 Respuesta recibida: {response_text[:100]}...")
            
            # Parsear resultado
            result = self._parse_response(response_text)
            return result
            
        except ValueError as e:
            logger.error(f"❌ Error decodificando imagen: {str(e)}")
            raise InvalidImageException(f"Imagen inválida: {str(e)}")
        except Exception as e:
            logger.error(f"❌ Error en análisis: {str(e)}")
            raise AnalysisFailedException(f"Análisis falló: {str(e)}")
    
    def _create_vision_prompt(self) -> str:
        """Crea prompt para análisis visual"""
        return """Eres un experto agrónomo IA especializado en diagnóstico de plantas.

Analiza la imagen adjunta de la planta y proporciona un diagnóstico estructurado en JSON:

{
  "estado": "Sana|Atención|Peligro",
  "confianza": 0.0-1.0,
  "sintomas": [
    {
      "nombre": "síntoma",
      "confianza": 0.0-1.0,
      "descripcion": "descripción detallada"
    }
  ],
  "especie_probable": "nombre de la especie",
  "análisis_visual": "análisis detallado visual"
}

REGLAS:
1. estado: Sana (sin problemas), Atención (problemas moderados), Peligro (problemas graves)
2. confianza: 0.0-1.0 (nivel de certeza del diagnóstico)
3. Analiza hojas, tallos, color, deformaciones
4. Responde SOLO con JSON válido
"""
    
    def _parse_response(self, response_text: str) -> VisionAnalysisResult:
        """Parsea respuesta del modelo a VisionAnalysisResult"""
        try:
            # Buscar JSON en respuesta
            import re
            json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', response_text, re.DOTALL)
            
            if json_match:
                json_str = json_match.group(0)
                data = json.loads(json_str)
            else:
                data = json.loads(response_text)
            
            # Parsear estado
            estado_str = data.get("estado", "Atención").strip()
            try:
                estado = PlantState[estado_str.upper()]
            except (KeyError, AttributeError):
                estado = PlantState.ATENCION
            
            # Parsear síntomas
            sintomas = []
            for sym in data.get("sintomas", []):
                sintomas.append(PlantSymptom(
                    nombre=sym.get("nombre", "Desconocido"),
                    confianza=float(sym.get("confianza", 0.5)),
                    descripcion=sym.get("descripcion", "")
                ))
            
            result = VisionAnalysisResult(
                estado=estado,
                confianza=float(data.get("confianza", 0.5)),
                sintomas=sintomas,
                especie_probable=data.get("especie_probable", "Desconocida"),
                análisis_visual=data.get("análisis_visual", "")
            )
            
            logger.info(f"✅ Respuesta parseada: {result.estado} (confianza: {result.confianza:.2f})")
            return result
            
        except Exception as e:
            logger.error(f"❌ Error parseando respuesta: {str(e)}")
            # Retornar resultado por defecto
            return VisionAnalysisResult(
                estado=PlantState.ATENCION,
                confianza=0.5,
                sintomas=[],
                especie_probable="Desconocida",
                análisis_visual="Error en análisis"
            )
