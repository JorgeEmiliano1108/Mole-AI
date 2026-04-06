# =============================================================================
# Copyright (C) 2024-2026 Mole.AI — All Rights Reserved.
# =============================================================================
import os
import uuid
import logging
from typing import List

from django.conf import settings
from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework import status
from celery.result import AsyncResult

from apps.ai_models.tasks import train_rag_async, train_vision_async, analyze_vision_async
from apps.ai_models.utils import safe_serialize

logger = logging.getLogger(__name__)

# --- CONFIGURACIÓN DE SEGURIDAD ---
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_IMAGE_TYPES = ['image/jpeg', 'image/png', 'image/webp']
ALLOWED_DATASET_TYPES = ['application/zip', 'application/x-zip-compressed']

def validate_file(file_obj, allowed_types: List[str]):
    if file_obj.size > MAX_FILE_SIZE:
        return False, "El archivo excede el límite de 10MB."
    if file_obj.content_type not in allowed_types:
        return False, f"Tipo de archivo no permitido: {file_obj.content_type}"
    return True, None

# --- VISTAS DE MONITOREO (PLACEHOLDERS RESTAURADOS) ---
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def llm_requests_view(request):
    return Response({'message': 'LLM Requests Monitoring', 'app': 'ai_models'})

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def cnn_inferences_view(request):
    return Response({'message': 'CNN Inferences Monitoring', 'app': 'ai_models'})

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def model_performance_view(request):
    return Response({'message': 'Model Performance', 'app': 'ai_models'})

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def ai_model_config_view(request):
    return Response({'message': 'AI Model Config', 'app': 'ai_models'})

class AIHealthCheckView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        return Response({'status': 'healthy', 'service': 'AI Models Module', 'version': '1.1.0'})

# --- VISTAS DE ENTRENAMIENTO ---
@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdminUser])
def train_rag_view(request):
    file_obj = request.FILES.get('file')
    if not file_obj:
        return Response({"error": "No file provided"}, status=400)
    
    is_valid, error_msg = validate_file(file_obj, ['application/pdf', 'text/plain'])
    if not is_valid:
        return Response({"error": error_msg}, status=400)
        
    try:
        temp_dir = os.path.join(settings.MEDIA_ROOT, 'temp')
        os.makedirs(temp_dir, exist_ok=True)
        temp_path = os.path.join(temp_dir, f"{uuid.uuid4().hex}_{file_obj.name}")
        
        with open(temp_path, 'wb+') as destination:
            for chunk in file_obj.chunks():
                destination.write(chunk)
                
        train_rag_async.delay(temp_path, file_obj.name, file_obj.content_type)  # type: ignore
        return Response({"status": "accepted", "task": "RAG_TRAIN"}, status=202)
    except Exception as e:
        return Response({"error": str(e)}, status=500)

@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdminUser])
def train_vision_view(request):
    datasets = request.FILES.getlist('dataset')
    if not datasets:
        return Response({"error": "No datasets provided"}, status=400)
        
    try:
        temp_dir = os.path.join(settings.MEDIA_ROOT, 'temp')
        os.makedirs(temp_dir, exist_ok=True)
        
        datasets_info = []
        for d in datasets:
            is_valid, _ = validate_file(d, ALLOWED_DATASET_TYPES)
            if not is_valid: continue

            temp_path = os.path.join(temp_dir, f"{uuid.uuid4().hex}_{d.name}")
            with open(temp_path, 'wb+') as destination:
                for chunk in d.chunks():
                    destination.write(chunk)
            datasets_info.append({'path': temp_path, 'name': d.name, 'type': d.content_type})

        train_vision_async.delay(datasets_info)  # type: ignore
        return Response({"status": "accepted", "count": len(datasets_info)}, status=202)
    except Exception as e:
        return Response({"error": str(e)}, status=500)

# --- VISTAS DE INFERENCIA ---
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def analyze_vision_view(request):
    file_obj = request.FILES.get('image') or request.FILES.get('file')
    if not file_obj:
        return Response({"error": "No image provided"}, status=400)

    is_valid, error_msg = validate_file(file_obj, ALLOWED_IMAGE_TYPES)
    if not is_valid:
        return Response({"error": error_msg}, status=400)

    try:
        temp_dir = os.path.join(settings.MEDIA_ROOT, 'temp')
        os.makedirs(temp_dir, exist_ok=True)
        temp_path = os.path.join(temp_dir, f"{uuid.uuid4().hex}_{file_obj.name}")

        with open(temp_path, 'wb+') as destination:
            for chunk in file_obj.chunks():
                destination.write(chunk)

        auth_header = str(request.headers.get('Authorization', ''))
        task = analyze_vision_async.delay(str(temp_path), auth_token=auth_header)  # type: ignore  

        return Response({"status": "accepted", "task_id": task.id}, status=202)
    except Exception as e:
        logger.exception("Error en analyze_vision_view")
        return Response({"error": str(e)}, status=500)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def vision_task_status_view(request, task_id):
    try:
        task = AsyncResult(task_id)
        state = task.state
        
        response_data = {
            'task_state': state,
            'result': safe_serialize(task.result) if state == 'SUCCESS' else None,
            'info': safe_serialize(task.info) if state != 'SUCCESS' else None
        }
        return Response(response_data)
    except Exception as exc:
        return Response({'error': 'Task status fetch failed', 'details': str(exc)})