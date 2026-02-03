"""Adapter Outbound: Phi-3.5 Reasoning Model"""

import logging
import asyncio
import json
import re

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

from ...domain.models import DiagnoseRequest, FinalDiagnosis
from ...domain.ports import ReasoningModelPort

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
            request: DiagnoseRequest con vision + sensores
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
                    do_sample=False
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
        """Crea prompt para razonamiento"""
        return f"""Eres un experto agrónomo IA. Genera un diagnóstico final estructurado en JSON:

ANÁLISIS VISUAL:
- Estado: {request.vision_output.estado}
- Confianza: {request.vision_output.confianza}
- Especie: {request.vision_output.especie_probable}
- Síntomas: {','.join(request.vision_output.sintomas)}

SENSORES:
- pH: {request.sensores.ph}
- Humedad: {request.sensores.humedad}%
- Temperatura: {request.sensores.temp}°C
- UV: {request.sensores.uv} mW/cm²

CONTEXTO RAG (Conocimiento Base):
{context}

DIAGNÓSTICO FINAL (JSON):
{{
  "diagnostico": "diagnóstico detallado",
  "recomendaciones": ["rec1", "rec2"],
  "fuentes_consultadas": ["fuente1"],
  "confianza_final": 0.85,
  "requiere_accion_humana": false
}}

Responde SOLO con JSON válido.
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
                diagnostico=data.get("diagnostico", "Análisis pendiente"),
                recomendaciones=data.get("recomendaciones", []),
                fuentes_consultadas=data.get("fuentes_consultadas", []),
                confianza_final=float(data.get("confianza_final", 0.5)),
                requiere_accion_humana=data.get("requiere_accion_humana", False)
            )
            
        except Exception as e:
            logger.error(f"❌ Error parseando diagnóstico: {str(e)}")
            return FinalDiagnosis(
                diagnostico="Error en análisis",
                recomendaciones=["Reintentar"],
                fuentes_consultadas=[],
                confianza_final=0.0,
                requiere_accion_humana=True
            )
