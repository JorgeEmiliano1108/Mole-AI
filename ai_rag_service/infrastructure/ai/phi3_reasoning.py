"""Adapter Outbound: Phi-3.5 Reasoning Model"""

import logging
import asyncio
import json
import re

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

from domain.models import DiagnoseRequest, FinalDiagnosis
from domain.interfaces import ReasoningModelPort

logger = logging.getLogger(__name__)


class Phi3ReasoningAdapter(ReasoningModelPort):
    """Implementación de ReasoningModelPort usando Phi-3.5"""
    
    def __init__(self, model_name: str = "microsoft/Phi-3.5-vision-instruct"):
        self.model_name = model_name
        self.model = None
        self.tokenizer = None
        self.device = "cpu"
        self._initialized = False
        logger.info(f"Phi3ReasoningAdapter inicializado")
    
    async def initialize(self):
        """Carga modelo Phi-3.5"""
        try:
            logger.info(f"⏳ Cargando {self.model_name}...")
            
            # ⚠️ TIMEOUT: 600 segundos (10 min) máximo para descargar Phi-3.5
            try:
                # Cargar tokenizer y modelo
                self.tokenizer = await asyncio.wait_for(
                    asyncio.to_thread(
                        AutoTokenizer.from_pretrained,
                        self.model_name,
                        trust_remote_code=True
                    ),
                    timeout=600.0  # 10 minutos máximo
                )
                
                self.model = await asyncio.wait_for(
                    asyncio.to_thread(
                        AutoModelForCausalLM.from_pretrained,
                        self.model_name,
                        device_map=self.device,
                        trust_remote_code=True,
                        torch_dtype=torch.float16,
                    ),
                    timeout=600.0  # 10 minutos máximo
                )
                
            except asyncio.TimeoutError:
                logger.error(f"⏱️ TIMEOUT: Phi-3.5 no se cargó en 10 minutos. Revisa conexión/almacenamiento.")
                raise RuntimeError(f"Model loading timeout after 600s")
            
            self.model.eval()
            self._initialized = True
            logger.info(f"✅ Phi-3.5 cargado exitosamente")
            
        except Exception as e:
            logger.error(f"❌ Error cargando Phi-3.5: {str(e)}")
            raise
    
    async def is_ready(self) -> bool:
        """Verifica si el modelo está listo"""
        return self._initialized and self.model is not None
    
    async def diagnose(self, request: DiagnoseRequest, context: str) -> FinalDiagnosis:
        """
        Genera diagnóstico final con Phi-3.5
        
        Args:
            request: DiagnoseRequest con vision + sensor_data
            context: Contexto recuperado del RAG
            
        Returns:
            FinalDiagnosis estructurado
        """
        try:
            # Crear prompt
            prompt = self._create_reasoning_prompt(request, context)
            
            # Tokenizar
            inputs = await asyncio.to_thread(
                self.tokenizer,
                prompt,
                return_tensors="pt"
            )
            
            # Mover a device
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            # Inferencia
            logger.info("🧠 Ejecutando razonamiento...")
            with torch.no_grad():
                outputs = await asyncio.to_thread(
                    self.model.generate,
                    **inputs,
                    max_new_tokens=512,
                    temperature=0.7,
                    do_sample=False,
                    use_cache=False  # FIX: DynamicCache 'seen_tokens' bug with Phi-3.5
                )
            
            # Decodificar
            response_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            logger.info(f"📝 Respuesta: {response_text[:100]}...")
            
            # Parsear diagnóstico
            diagnosis = self._parse_diagnosis(response_text)
            return diagnosis
            
        except Exception as e:
            logger.error(f"❌ Error en diagnóstico: {str(e)}")
            raise
    
    def _create_reasoning_prompt(self, request: DiagnoseRequest, context: str) -> str:
        """Crea prompt para razonamiento con CITAS OBLIGATORIAS"""
        # Extract vision info safely
        vision_desc = request.vision_output.description if request.vision_output else "N/A"
        vision_conf = request.vision_output.confidence if request.vision_output else "N/A"
        vision_tags = ','.join(request.vision_output.tags) if request.vision_output and request.vision_output.tags else "N/A"
        
        # Extract sensor info safely
        sensor_ph = request.sensor_data.ph_level if request.sensor_data and request.sensor_data.ph_level is not None else "N/A"
        sensor_humidity = request.sensor_data.humidity if request.sensor_data and request.sensor_data.humidity is not None else "N/A"
        sensor_temp = request.sensor_data.temperature if request.sensor_data and request.sensor_data.temperature is not None else "N/A"
        sensor_uv = request.sensor_data.uv_index if request.sensor_data and request.sensor_data.uv_index is not None else "N/A"
        
        return f"""Eres un experto agrónomo IA. Genera un diagnóstico final estructurado en JSON CON CITAS OBLIGATORIAS:

ANÁLISIS VISUAL:
- Descripción: {vision_desc}
- Confianza: {vision_conf}
- Tags: {vision_tags}

SENSORES:
- pH: {sensor_ph}
- Humedad: {sensor_humidity}%
- Temperatura: {sensor_temp}°C
- UV: {sensor_uv} mW/cm²

CONTEXTO RAG CON FUENTES VERIFICABLES:
{context}

DIAGNÓSTICO FINAL (JSON CON CITAS OBLIGATORIAS):
{{
  "diagnosis": "diagnóstico detallado basado en las fuentes citadas",
  "recommendations": [
    "rec1 basada en [GBIF:12345]",
    "rec2 basada en [USDA:TOM]"
  ],
  "sources_consulted": [
    {{
      "type": "GBIF",
      "id": "12345",
      "url": "https://www.gbif.org/species/12345",
      "confidence": 0.9
    }},
    {{
      "type": "USDA",
      "id": "TOM",
      "url": "https://plants.usda.gov/java/profile?symbol=TOM",
      "confidence": 0.85
    }}
  ],
  "final_confidence": 0.85,
  "requires_human_action": false,
  "references": "Citar explícitamente cada fuente usada en el diagnóstico"
}}

REGLAS ESTRICTAS DE CITACIÓN:
1. CADA afirmación científica debe incluir su fuente [GBIF:12345] o [USDA:TOM]
2. Sin inventar datos sin fuente verificable
3. Las URLs deben ser funcionales y verificables
4. Usar únicamente las fuentes proporcionadas en el contexto
5. Formato de cita obligatorio: [TIPO:ID] en el texto
6. Las fuentes deben estar listadas en el array sources_consulted

Responde SOLO con JSON válido que incluya todas las citas requeridas.
"""
    
    def _parse_diagnosis(self, response_text: str) -> FinalDiagnosis:
        """Parsea respuesta a FinalDiagnosis"""
        try:
            # Buscar JSON
            json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', response_text, re.DOTALL)
            
            if json_match:
                json_str = json_match.group(0)
                data = json.loads(json_str)
            else:
                data = json.loads(response_text)
            
            return FinalDiagnosis(
                diagnosis=data.get("diagnosis", "Análisis pendiente"),
                recommendations=data.get("recommendations", []),
                sources_consulted=data.get("sources_consulted", []),
                final_confidence=float(data.get("final_confidence", 0.5)),
                requires_human_action=data.get("requires_human_action", False)
            )
            
        except Exception as e:
            logger.error(f"❌ Error parseando diagnóstico: {str(e)}")
            return FinalDiagnosis(
                diagnosis="Error en análisis",
                recommendations=["Reintentar"],
                sources_consulted=[],
                final_confidence=0.0,
                requires_human_action=True
            )