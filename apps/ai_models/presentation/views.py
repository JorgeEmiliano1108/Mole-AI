# =============================================================================
# Copyright (C) 2024-2026 Mole.AI — All Rights Reserved.
#
# AVISO DE PROPIEDAD INTELECTUAL:
# Este archivo es propiedad exclusiva de Mole.AI y sus autores originales.
# Queda estrictamente prohibida la copia, modificación, distribución,
# sublicenciamiento o uso comercial de este código, total o parcialmente,
# sin la autorización expresa y por escrito de los titulares del Copyright.
#
# Cualquier uso no autorizado será perseguido conforme a la Ley Federal
# del Derecho de Autor (México) y tratados internacionales aplicables.
# =============================================================================
from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework import status
import requests


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def llm_requests_view(request):
    """
    API endpoint para gestionar peticiones LLM
    """
    return Response({
        'message': 'LLM Requests - Endpoint placeholder',
        'status': 'implemented',
        'app': 'ai_models'
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def cnn_inferences_view(request):
    """
    API endpoint para gestionar inferencias CNN
    """
    return Response({
        'message': 'CNN Inferences - Endpoint placeholder',
        'status': 'implemented',
        'app': 'ai_models'
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def model_performance_view(request):
    """
    API endpoint para métricas de rendimiento de modelos
    """
    return Response({
        'message': 'Model Performance - Endpoint placeholder',
        'status': 'implemented',
        'app': 'ai_models'
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def ai_model_config_view(request):
    """
    API endpoint para configuración de modelos IA
    """
    return Response({
        'message': 'AI Model Configuration - Endpoint placeholder',
        'status': 'implemented',
        'app': 'ai_models'
    })


class AIHealthCheckView(APIView):
    """
    Health check para el módulo de IA
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        return Response({
            'status': 'healthy',
            'service': 'AI Models Module',
            'version': '1.0.0'
        })

@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdminUser])
def train_rag_view(request):
    """
    API endpoint para entrenar modelo RAG (Acepta archivos)
    """
    file_obj = request.FILES.get('file')
    if not file_obj:
        return Response({"error": "No file provided"}, status=status.HTTP_400_BAD_REQUEST)
        
    try:
        import os
        import uuid
        from django.conf import settings
        from apps.ai_models.tasks import train_rag_async
        
        temp_dir = os.path.join(settings.MEDIA_ROOT, 'temp')
        os.makedirs(temp_dir, exist_ok=True)
        temp_path = os.path.join(temp_dir, f"{uuid.uuid4().hex}_{file_obj.name}")
        
        with open(temp_path, 'wb+') as destination:
            for chunk in file_obj.chunks():
                destination.write(chunk)
                
        train_rag_async.delay(temp_path, file_obj.name, file_obj.content_type)
        return Response({"status": "accepted", "message": "Entrenamiento RAG encolado de manera asíncrona"}, status=status.HTTP_202_ACCEPTED)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdminUser])
def train_vision_view(request):
    """
    API endpoint para entrenar modelo CNN Vision (Acepta archivos)
    """
    datasets = request.FILES.getlist('dataset')
    if not datasets:
        return Response({"error": "No datasets provided"}, status=status.HTTP_400_BAD_REQUEST)
        
    try:
        import os
        import uuid
        from django.conf import settings
        from apps.ai_models.tasks import train_vision_async

        temp_dir = os.path.join(settings.MEDIA_ROOT, 'temp')
        os.makedirs(temp_dir, exist_ok=True)
        
        datasets_info = []
        for d in datasets:
            temp_path = os.path.join(temp_dir, f"{uuid.uuid4().hex}_{d.name}")
            with open(temp_path, 'wb+') as destination:
                for chunk in d.chunks():
                    destination.write(chunk)
            datasets_info.append({'path': temp_path, 'name': d.name, 'type': d.content_type})

        train_vision_async.delay(datasets_info)
        return Response({"status": "accepted", "message": "Entrenamiento CNN encolado de manera asíncrona"}, status=status.HTTP_202_ACCEPTED)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def analyze_vision_view(request):
    """
    POST /api/v1/ai/vision/analyze/
    Endpoint de análisis de visión, guarda temporalmente la imagen y dispara Celery.
    """
    file_obj = request.FILES.get('image') or request.FILES.get('file')
    if not file_obj:
        return Response({"error": "No image provided"}, status=status.HTTP_400_BAD_REQUEST)
        
    try:
        import os
        import uuid
        from django.conf import settings
        from apps.ai_models.tasks import analyze_vision_async
        
        temp_dir = os.path.join(settings.MEDIA_ROOT, 'temp')
        os.makedirs(temp_dir, exist_ok=True)
        temp_path = os.path.join(temp_dir, f"{uuid.uuid4().hex}_{file_obj.name}")
        
        with open(temp_path, 'wb+') as destination:
            for chunk in file_obj.chunks():
                destination.write(chunk)
                
        task = analyze_vision_async.delay(temp_path, file_obj.name, file_obj.content_type)
        return Response({
            "status": "accepted", 
            "message": "Protocolo de extracción iniciado", 
            "task_id": task.id
        }, status=status.HTTP_202_ACCEPTED)
        
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

from celery.result import AsyncResult

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def vision_task_status_view(request, task_id):
    """
    GET /api/v1/ai/vision/status/{task_id}/
    Polling endpoint para ver el estado de la tarea de Celery.
    """
    task = AsyncResult(task_id)
    if task.state == 'SUCCESS':
        return Response({
            "state": task.state,
            "result": task.result
        }, status=status.HTTP_200_OK)
    elif task.state == 'FAILURE':
        return Response({
            "state": task.state,
            "error": str(task.info)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    else:
        return Response({
            "state": task.state,
            "status": "Processing..."
        }, status=status.HTTP_200_OK)