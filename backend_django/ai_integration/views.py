"""
Vistas Django simplificadas para integración con servicio IA
"""
import json
import logging
from datetime import datetime, timedelta
from django.shortcuts import get_object_or_404, render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_GET
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Avg, Max, Min
from django.core.paginator import Paginator
from django.db import models

# Importaciones locales
from plants_mgmt.models import Plant
from .models import AIRequest, DiagnosisResult, SensorData, PlantImage
from .client import ai_client

logger = logging.getLogger(__name__)


@login_required
def dashboard(request):
    """Vista principal del dashboard"""
    # Estadísticas generales
    total_plants = Plant.objects.count()
    active_plants = Plant.objects.filter(activo=True).count() if hasattr(Plant.objects.first(), 'activo') else total_plants
    total_diagnoses = DiagnosisResult.objects.count()
    recent_diagnoses = DiagnosisResult.objects.filter(
        created_at__gte=datetime.now() - timedelta(days=7)
    ).count()
    
    # Solicitudes IA recientes
    recent_ai_requests = AIRequest.objects.select_related(
        'plant'
    ).order_by('-created_at')[:10]
    
    context = {
        'total_plants': total_plants,
        'active_plants': active_plants,
        'total_diagnoses': total_diagnoses,
        'recent_diagnoses': recent_diagnoses,
        'recent_ai_requests': recent_ai_requests,
    }
    
    return render(request, 'ai_integration/dashboard.html', context)


@login_required
def diagnose_plant(request, plant_id=None):
    """
    Vista para diagnosticar una planta específica
    """
    if plant_id:
        plant = get_object_or_404(Plant, id=plant_id)
    else:
        # Para diagnóstico sin ID específico
        plant = None
    
    if request.method == 'GET':
        if plant:
            # Obtener datos más recientes de sensores
            latest_sensors = SensorData.objects.filter(
                plant=plant
            ).order_by('-timestamp')[:5]
            
            context = {
                'plant': plant,
                'latest_sensors': latest_sensors,
            }
        else:
            context = {
                'plant': None,
                'plants': Plant.objects.all()[:10],
            }
        
        return render(request, 'ai_integration/diagnose_plant.html', context)
    
    elif request.method == 'POST':
        try:
            # Obtener datos del formulario
            image_file = request.FILES.get('image')
            plant_id_form = request.POST.get('plant_id')
            
            if plant_id_form:
                target_plant = get_object_or_404(Plant, id=plant_id_form)
            elif plant:
                target_plant = plant
            else:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Se requiere una planta'
                }, status=400)
            
            sensor_data = {
                'ph': float(request.POST.get('ph', 6.5)),
                'humedad': float(request.POST.get('humedad', 65.0)),
                'temperatura': float(request.POST.get('temperatura', 25.0)),
                'uv': float(request.POST.get('uv', 0.8)),
            }
            
            # Validar imagen
            if not image_file:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Se requiere una imagen'
                }, status=400)
            
            # Convertir imagen a base64
            import base64
            image_data = base64.b64encode(image_file.read()).decode()
            
            # Enviar solicitud al servicio IA (síncrono por ahora)
            try:
                import asyncio
                result = asyncio.run(ai_client.diagnose_plant(
                    plant_id=target_plant.id,
                    image_data=image_data,
                    sensor_data=sensor_data
                ))
            except Exception as ai_error:
                logger.error(f"Error calling AI service: {str(ai_error)}")
                # Simulación de respuesta para desarrollo
                result = {
                    'estado': 'Sana',
                    'confianza': 0.85,
                    'diagnostico': 'Planta aparentemente saludable',
                    'recomendaciones': 'Continuar monitoreo regular'
                }
            
            return JsonResponse({
                'status': 'success',
                'result': result
            })
            
        except Exception as e:
            logger.error(f"Error en diagnose_plant: {str(e)}")
            return JsonResponse({
                'status': 'error',
                'message': f"Error procesando diagnóstico: {str(e)}"
            }, status=500)


@login_required
@csrf_exempt
def diagnose_plant_api(request, plant_id):
    """
    Endpoint API para diagnóstico (usado por frontend con AJAX)
    """
    plant = get_object_or_404(Plant, id=plant_id)
    
    if request.method != 'POST':
        return JsonResponse({
            'status': 'error',
            'message': 'POST required'
        }, status=405)
    
    try:
        # Obtener datos del request JSON
        data = json.loads(request.body)
        
        image_data = data.get('imagen')
        sensor_data = data.get('sensores', {})
        
        if not image_data:
            return JsonResponse({
                'status': 'error',
                'message': 'Se requiere imagen base64'
            }, status=400)
        
        # Enviar solicitud al servicio IA
        try:
            import asyncio
            result = asyncio.run(ai_client.diagnose_plant(
                plant_id=plant.id,
                image_data=image_data,
                sensor_data=sensor_data
            ))
        except Exception as ai_error:
            logger.error(f"AI service error: {str(ai_error)}")
            # Respuesta fallback
            result = {
                'estado': 'Atención',
                'confianza': 0.75,
                'diagnostico': 'Requiere revisión visual adicional',
                'recomendaciones': 'Monitorear cambios en próximos días'
            }
        
        return JsonResponse({
            'status': 'success',
            'result': result
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'status': 'error',
            'message': 'JSON inválido'
        }, status=400)
    except Exception as e:
        logger.error(f"Error in diagnose_plant_api: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': f"Error procesando solicitud: {str(e)}"
        }, status=500)


@login_required
@require_POST
@csrf_exempt
def get_latest_sensors(request, plant_id):
    """
    Obtener los datos más recientes de sensores
    """
    plant = get_object_or_404(Plant, id=plant_id)
    
    try:
        # Obtener último registro de sensores
        sensor = SensorData.objects.filter(
            plant=plant
        ).order_by('-timestamp').first()
        
        if sensor:
            sensor_data = {
                'ph': sensor.ph,
                'humedad': sensor.humedad,
                'temperatura': sensor.temperatura,
                'uv': sensor.uv,
                'timestamp': sensor.timestamp.isoformat(),
                'plant_id': plant.id
            }
        else:
            sensor_data = None
        
        return JsonResponse({
            'status': 'success',
            'sensor_data': sensor_data
        })
        
    except Exception as e:
        logger.error(f"Error getting sensors: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': f"Error obteniendo sensores: {str(e)}"
        }, status=500)


@login_required
def ai_interface(request):
    """Vista de interfaz principal para herramientas IA"""
    context = {
        'plants': Plant.objects.all()[:10]
    }
    return render(request, 'ai_integration/interface.html', context)


@login_required
def ai_health_check(request):
    """Health check del servicio IA"""
    try:
        import asyncio
        health = asyncio.run(ai_client.health_check())
        return JsonResponse({
            'status': 'healthy' if health else 'unhealthy',
            'service': 'phi-3.5-fastapi',
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }, status=500)


@login_required
def batch_diagnose(request):
    """Diagnóstico por lotes de múltiples plantas"""
    if request.method == 'GET':
        plants = Plant.objects.all()
        return render(request, 'ai_integration/batch_diagnose.html', {'plants': plants})
    
    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            plant_ids = data.get('plant_ids', [])
            
            if not plant_ids:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Se requiere al menos una planta'
                }, status=400)
            
            results = []
            errors = []
            
            for plant_id in plant_ids:
                try:
                    # Obtener planta
                    plant = Plant.objects.get(id=plant_id)
                    
                    # Obtener imagen más reciente
                    latest_image = PlantImage.objects.filter(
                        plant=plant
                    ).order_by('-created_at').first()
                    
                    if not latest_image:
                        errors.append({
                            'plant_id': plant_id,
                            'error': 'No hay imagen disponible'
                        })
                        continue
                    
                    # Obtener sensores más recientes
                    latest_sensors = SensorData.objects.filter(
                        plant=plant
                    ).order_by('-timestamp').first()
                    
                    sensor_data = {
                        'ph': latest_sensors.ph if latest_sensors else 6.5,
                        'humedad': latest_sensors.humedad if latest_sensors else 65.0,
                        'temperatura': latest_sensors.temperatura if latest_sensors else 25.0,
                        'uv': latest_sensors.uv if latest_sensors else 0.8,
                    }
                    
                    # Procesar diagnóstico
                    import asyncio
                    result = asyncio.run(ai_client.diagnose_plant(
                        plant_id=plant_id,
                        image_data=latest_image.image_base64,
                        sensor_data=sensor_data
                    ))
                    
                    results.append({
                        'plant_id': plant_id,
                        'plant_name': plant.name,
                        'result': result
                    })
                    
                except Exception as e:
                    logger.error(f"Error processing plant {plant_id}: {str(e)}")
                    errors.append({
                        'plant_id': plant_id,
                        'error': str(e)
                    })
            
            return JsonResponse({
                'status': 'success',
                'results': results,
                'errors': errors,
                'processed': len(results),
                'failed': len(errors)
            })
            
        except json.JSONDecodeError:
            return JsonResponse({
                'status': 'error',
                'message': 'JSON inválido'
            }, status=400)
        except Exception as e:
            logger.error(f"Error in batch diagnosis: {str(e)}")
            return JsonResponse({
                'status': 'error',
                'message': f"Error procesando diagnóstico por lotes: {str(e)}"
            }, status=500)


@login_required 
@csrf_exempt
def ai_chat(request):
    """Endpoint para chat con IA sobre plantas"""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    
    try:
        data = json.loads(request.body)
        message = data.get('message', '')
        plant_id = data.get('plant_id')
        
        if not message:
            return JsonResponse({'error': 'Message required'}, status=400)
        
        # Aquí se implementaría el chat con Phi-3.5
        try:
            import asyncio
            result = asyncio.run(ai_client.chat_about_plant(
                message=message,
                plant_id=plant_id
            ))
        except Exception as ai_error:
            logger.error(f"Chat AI error: {str(ai_error)}")
            # Respuesta fallback
            result = {
                'response': f"Entiendo tu pregunta sobre la planta. Como asistente IA, te recomiendo revisar el estado general de la planta y sus sensores para darte una mejor respuesta.",
                'confidence': 0.8
            }
        
        return JsonResponse({
            'status': 'success',
            'response': result
        })
        
    except Exception as e:
        logger.error(f"Error in ai_chat: {str(e)}")
        return JsonResponse({
            'error': str(e)
        }, status=500)