"""
Hugging Face Vision Client for Phi-3.5 Vision Integration

This module provides a complete client for interacting with Microsoft Phi-3.5 Vision
through the Hugging Face Inference API with proper error handling and formatting.
"""

import requests
import base64
import json
import logging
from typing import Dict, Any, Optional
from django.conf import settings
from datetime import datetime

logger = logging.getLogger('ai_models')

class HuggingFaceVisionClient:
    """
    Cliente especializado para Hugging Face Inference API con Phi-3.5 Vision
    
    Proporciona métodos para analizar imágenes usando el formato específico
    requerido por Phi-3.5 Vision con manejo robusto de errores.
    """
    
    def __init__(self):
        """Inicializa el cliente con configuración desde settings.py"""
        self.api_key = getattr(settings, 'HUGGINGFACE_API_KEY', None)
        self.model_name = getattr(settings, 'HF_MODEL_NAME', 'microsoft/Phi-3.5-vision-instruct')
        self.api_url = getattr(settings, 'HF_INFERENCE_API_URL', 
                               'https://api-inference.huggingface.co/models/microsoft/Phi-3.5-vision-instruct')
        self.timeout = getattr(settings, 'HF_API_TIMEOUT', 30)
        self.max_retries = getattr(settings, 'HF_MAX_RETRIES', 3)
        
        if not self.api_key:
            raise ValueError("HUGGINGFACE_API_KEY no está configurada en settings.py")
        
        # Setup session para reutilizar conexiones
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        })
        
        logger.info(f"HuggingFace Vision Client initialized for model: {self.model_name}")
    
    def prepare_image_for_analysis(self, image_file) -> str:
        """
        Convierte imagen a base64 para enviar a HF API
        
        Args:
            image_file: Archivo de imagen (InMemoryUploadedFile)
            
        Returns:
            str: Imagen codificada en base64
        """
        try:
            # Leer el contenido del archivo
            image_data = image_file.read()
            
            # Codificar en base64
            image_b64 = base64.b64encode(image_data).decode('utf-8')
            
            logger.info(f"Image encoded to base64, size: {len(image_b64)} chars")
            return image_b64
            
        except Exception as e:
            logger.error(f"Error preparing image: {str(e)}")
            raise ValueError(f"No se pudo procesar la imagen: {str(e)}")
    
    def analyze_plant_image(self, image_data: str, prompt_usuario: str = None) -> Dict[str, Any]:
        """
        Analiza imagen de planta usando Phi-3.5 Vision
        
        Args:
            image_data: Imagen codificada en base64
            prompt_usuario: Prompt personalizado del usuario
            
        Returns:
            Dict: Resultado del análisis con predicciones
        """
        if not prompt_usuario:
            prompt_usuario = "Analiza esta imagen de planta y describe cualquier enfermedad o condición visible. Sé específico sobre síntomas y posibles tratamientos."
        
        # Formato Phi-3.5 Vision - REQUISITO CRÍTICO
        prompt_phi35 = f"<|user|>\n<|image_1|>\n{prompt_usuario}<|end|>\n<|assistant|>\n"
        
        # Payload para HF Inference API
        payload = {
            "inputs": prompt_phi35,
            "parameters": {
                "max_new_tokens": 500,
                "temperature": 0.7,
                "do_sample": True,
                "top_p": 0.9,
                "return_full_text": False
            }
        }
        
        # Estructura específica para Phi-3.5 Vision con imagen
        if image_data:
            payload["inputs"] = {
                "text": prompt_phi35,
                "images": [image_data]
            }
        
        logger.info(f"Sending request to HF API: {self.api_url}")
        logger.debug(f"Payload structure: {list(payload.keys())}")
        
        for attempt in range(self.max_retries):
            try:
                start_time = datetime.now()
                
                response = self.session.post(
                    self.api_url,
                    json=payload,
                    timeout=self.timeout
                )
                
                processing_time = int((datetime.now() - start_time).total_seconds() * 1000)
                
                if response.status_code == 200:
                    result = response.json()
                    logger.info(f"Analysis completed in {processing_time}ms")
                    return self._parse_hf_response(result, processing_time)
                
                elif response.status_code == 503:
                    logger.warning(f"Model loading (attempt {attempt + 1})...")
                    if attempt < self.max_retries - 1:
                        import time
                        time.sleep(2 ** attempt)  # Exponential backoff
                        continue
                
                else:
                    logger.error(f"HF API Error {response.status_code}: {response.text}")
                    return {
                        'success': False,
                        'error': f"API Error {response.status_code}",
                        'processing_time_ms': processing_time
                    }
                    
            except requests.exceptions.Timeout:
                logger.error(f"Timeout after {self.timeout}s (attempt {attempt + 1})")
                if attempt == self.max_retries - 1:
                    return {
                        'success': False,
                        'error': 'Timeout en la API de Hugging Face',
                        'processing_time_ms': self.timeout * 1000
                    }
                    
            except requests.exceptions.ConnectionError:
                logger.error(f"Connection error (attempt {attempt + 1})")
                if attempt == self.max_retries - 1:
                    return {
                        'success': False,
                        'error': 'Error de conexión con Hugging Face',
                        'processing_time_ms': 0
                    }
                    
            except Exception as e:
                logger.error(f"Unexpected error (attempt {attempt + 1}): {str(e)}")
                if attempt == self.max_retries - 1:
                    return {
                        'success': False,
                        'error': f'Error inesperado: {str(e)}',
                        'processing_time_ms': 0
                    }
        
        return {
            'success': False,
            'error': 'Máximo de reintentos alcanzado',
            'processing_time_ms': 0
        }
    
    def _parse_hf_response(self, hf_response: list, processing_time_ms: int) -> Dict[str, Any]:
        """
        Parsea la respuesta de Hugging Face al formato esperado por la app
        
        Args:
            hf_response: Respuesta cruda de HF API
            processing_time_ms: Tiempo de procesamiento en ms
            
        Returns:
            Dict: Respuesta formateada
        """
        try:
            if not hf_response or not isinstance(hf_response, list):
                raise ValueError("Respuesta inválida de HF API")
            
            # Extraer texto generado
            generated_text = hf_response[0].get('generated_text', '')
            
            if not generated_text:
                raise ValueError("No se generó texto en la respuesta")
            
            # Simular estructura de predicciones basada en el texto
            predictions = self._extract_predictions_from_text(generated_text)
            
            return {
                'success': True,
                'predictions': predictions,
                'confidence_scores': [pred.get('confidence', 0.5) for pred in predictions],
                'top_prediction': predictions[0] if predictions else {},
                'raw_response': generated_text,
                'processing_time_ms': processing_time_ms,
                'model_used': self.model_name
            }
            
        except Exception as e:
            logger.error(f"Error parsing HF response: {str(e)}")
            return {
                'success': False,
                'error': f'Error procesando respuesta: {str(e)}',
                'processing_time_ms': processing_time_ms
            }
    
    def _extract_predictions_from_text(self, text: str) -> list:
        """
        Extrae predicciones estructuradas del texto generado por Phi-3.5
        
        Args:
            text: Texto generado por el modelo
            
        Returns:
            list: Lista de predicciones con estructura estándar
        """
        predictions = []
        
        # Análisis simple del texto para extraer condiciones
        text_lower = text.lower()
        
        if 'sana' in text_lower or 'saludable' in text_lower:
            predictions.append({
                'label': 'Planta Saludable',
                'confidence': 0.85,
                'description': 'La planta no muestra signos visibles de enfermedad'
            })
        
        # Buscar enfermedades comunes
        disease_keywords = {
            'deficiencia de nitrógeno': 0.75,
            'deficiencia de hierro': 0.70,
            'exceso de riego': 0.65,
            'falta de riego': 0.60,
            'hongos': 0.80,
            'mosaic': 0.75,
            'manchas': 0.65,
            'amarillamiento': 0.60
        }
        
        for keyword, confidence in disease_keywords.items():
            if keyword in text_lower:
                predictions.append({
                    'label': keyword.title(),
                    'confidence': confidence,
                    'description': f'Se detectaron síntomas de {keyword}'
                })
        
        # Si no se encontró nada específico, dar un diagnóstico general
        if not predictions:
            predictions.append({
                'label': 'Condición Desconocida',
                'confidence': 0.40,
                'description': 'Se requiere análisis adicional por un experto'
            })
        
        # Ordenar por confianza
        predictions.sort(key=lambda x: x['confidence'], reverse=True)
        
        return predictions[:3]  # Top 3 predicciones
    
    def health_check(self) -> Dict[str, Any]:
        """
        Verifica si el servicio de HF está disponible
        
        Returns:
            Dict: Estado del servicio
        """
        try:
            response = self.session.get(f"{self.api_url}/status", timeout=10)
            
            if response.status_code == 200:
                return {
                    'status': 'healthy',
                    'model': self.model_name,
                    'endpoint': self.api_url
                }
            else:
                return {
                    'status': 'unhealthy',
                    'error': f"Status code: {response.status_code}"
                }
                
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }


def consultar_phi_vision(image_file, prompt_usuario: str) -> Dict[str, Any]:
    """
    Función principal para analizar imagen con Phi-3.5 Vision
    
    Args:
        image_file: Archivo de imagen
        prompt_usuario: Prompt personalizado del usuario
        
    Returns:
        Dict: Resultado del análisis compatible con la estructura existente
    """
    try:
        # Inicializar cliente
        client = HuggingFaceVisionClient()
        
        # Preparar imagen
        image_b64 = client.prepare_image_for_analysis(image_file)
        
        # Analizar imagen
        result = client.analyze_plant_image(image_b64, prompt_usuario)
        
        return result
        
    except Exception as e:
        logger.error(f"Error in consultar_phi_vision: {str(e)}")
        return {
            'success': False,
            'error': f'Error general: {str(e)}',
            'processing_time_ms': 0
        }
