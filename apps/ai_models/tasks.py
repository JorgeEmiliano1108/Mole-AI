import os
import logging
import requests
import time
from celery import shared_task
from celery.exceptions import Retry, MaxRetriesExceededError
from django.conf import settings

logger = logging.getLogger(__name__)

# --- TAREA DE LIMPIEZA AUTOMÁTICA (GARBAGE COLLECTOR) ---
@shared_task(name="cleanup_temp_files")
def cleanup_temp_files():
    """
    Tarea programada para limpiar archivos temporales de más de 24 horas.
    Debe configurarse en Celery Beat para ejecutarse diariamente.
    """
    temp_dir = os.path.join(settings.MEDIA_ROOT, 'temp')
    if not os.path.exists(temp_dir):
        return "Temp directory does not exist."

    now = time.time()
    deleted_count = 0
    
    for f in os.listdir(temp_dir):
        f_path = os.path.join(temp_dir, f)
        # Si el archivo tiene más de 24 horas (86400 segundos)
        if os.stat(f_path).st_mtime < now - 86400:
            try:
                os.remove(f_path)
                deleted_count += 1
            except Exception as e:
                logger.error(f"Error deleting temp file {f_path}: {e}")

    return f"Cleanup finished. Deleted {deleted_count} files."

# --- TAREAS DE ENTRENAMIENTO ---
@shared_task(bind=True, max_retries=3, name="train_rag_async")
def train_rag_async(self, file_path, original_filename, content_type):
    try:
        with open(file_path, 'rb') as f:
            files = {'file': (original_filename, f, content_type)}
            response = requests.post("http://fastapi_rag:8002/api/v1/train/", files=files, timeout=60)
            response.raise_for_status()
        
        if os.path.exists(file_path): os.remove(file_path)
        return "RAG Training successful"
    except Exception as exc:
        if isinstance(exc, requests.exceptions.ConnectionError):
            raise self.retry(exc=exc, countdown=5)
        if os.path.exists(file_path): os.remove(file_path)
        raise

@shared_task(bind=True, max_retries=3, name="analyze_vision_async")
def analyze_vision_async(self, file_path, auth_token=''):
    """Inferencia de visión vía MS1 con manejo robusto de archivos."""
    try:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Missing file: {file_path}")

        with open(file_path, 'rb') as f:
            files = {'file': (os.path.basename(file_path), f)}
            headers = {'Authorization': auth_token} if auth_token else {}
            
            response = requests.post(
                "http://ms1_vision:8001/api/v1/vision/analyze",
                files=files,
                headers=headers,
                timeout=30
            )
            response.raise_for_status()

        if os.path.exists(file_path): os.remove(file_path)
        return response.json()
        
    except requests.exceptions.ConnectionError as exc:
        raise self.retry(exc=exc, countdown=2)
    except Exception as exc:
        if os.path.exists(file_path): os.remove(file_path)
        logger.error(f"Vision Analysis Task Failed: {exc}")
        raise

# CORRECCIÓN: Indentación alineada al nivel del módulo
@shared_task(bind=True, max_retries=3, name="train_vision_async")
def train_vision_async(self, datasets_info):
    """
    datasets_info: list of dicts with 'path', 'name', 'type'
    """
    file_objs = []
    try:
        files = []
        for info in datasets_info:
            f = open(info['path'], 'rb')
            file_objs.append(f)
            files.append(('dataset', (info['name'], f, info['type'])))
            
        response = requests.post("http://ms1_vision:8001/api/v1/train/", files=files, timeout=60)
        
        for f in file_objs:
            f.close()
            
        response.raise_for_status()
        
        # Éxito: limpiar
        for info in datasets_info:
            if os.path.exists(info['path']):
                os.remove(info['path'])
                
        return "Vision Training started successfully"
    except requests.exceptions.ConnectionError as exc:
        for f in file_objs:
            f.close()
        try:
            raise self.retry(exc=exc, countdown=2)
        except MaxRetriesExceededError:
            for info in datasets_info:
                if os.path.exists(info['path']):
                    os.remove(info['path'])
            raise
    except Exception:
        for f in file_objs:
            f.close()
        for info in datasets_info:
            if os.path.exists(info['path']):
                os.remove(info['path'])
        raise