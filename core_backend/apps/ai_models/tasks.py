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
            # B2 FIX: hostname corregido de 'fastapi_rag' → 'ms2_chat'
            response = requests.post("http://ms2_chat:8002/api/v1/knowledge/ingest-pdf", files=files, timeout=60)
            response.raise_for_status()
        
        if os.path.exists(file_path): os.remove(file_path)
        return "RAG Training successful"
    except Exception as exc:
        if isinstance(exc, requests.exceptions.ConnectionError):
            raise self.retry(exc=exc, countdown=5)
        if os.path.exists(file_path): os.remove(file_path)
        raise

@shared_task(bind=True, max_retries=3, name="analyze_vision_async")
def analyze_vision_async(self, file_path, auth_token='', user_id=None, plant_id=None):
    """
    Inferencia de visión vía MS1 con manejo robusto de archivos.
    Guarda resultado en AIDiagnostic para trazabilidad.
    """
    import uuid
    from django.utils import timezone
    
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
        
        result = response.json()
        
        # Guardar resultado en base de datos (trazabilidad LFPDPPP)
        if user_id:
            try:
                from apps.core.models import AIDiagnostic
                from apps.authentication.models import User
                
                user = User.objects.get(id=user_id)
                
                diagnostic = AIDiagnostic.objects.create(
                    user=user,
                    plant_id=plant_id or uuid.uuid4(),
                    image_path=file_path,
                    diagnosis_label=result.get("condition"),
                    confidence_score=result.get("confidence"),
                    metadata={
                        "species": result.get("species"),
                        "severity": result.get("severity"),
                        "ph_predicted": result.get("ph_predicted"),
                        "task_id": self.request.id,
                    }
                )
                logger.info(f"AIDiagnostic saved: {diagnostic.id} for user {user_id}")
                
                # Agregar task_id al resultado para polling
                result["diagnostic_id"] = str(diagnostic.id)
            except Exception as e:
                logger.error(f"Failed to save AIDiagnostic: {e}")

        if os.path.exists(file_path): os.remove(file_path)
        return result
        
    except requests.exceptions.ConnectionError as exc:
        raise self.retry(exc=exc, countdown=2)
    except Exception as exc:
        if os.path.exists(file_path): os.remove(file_path)
        logger.error(f"Vision Analysis Task Failed: {exc}")
        raise

# B1 FIX: MS1 no tiene endpoint /train/. Usamos Redis Pub/Sub para
# notificar al microservicio de visión que hay nuevos datasets disponibles.
# MS1 ya escucha el canal 'mole:training:new_asset' de forma pasiva.
@shared_task(bind=True, max_retries=3, name="train_vision_async")
def train_vision_async(self, datasets_info):
    """
    Emite un evento Redis Pub/Sub para que MS1 procese los datasets
    de forma asíncrona (arquitectura event-driven — Fase 3 MLOps).

    datasets_info: list of dicts with 'path', 'name', 'type'
    """
    import json as _json
    import redis as _redis
    from django.conf import settings as _settings

    try:
        r = _redis.from_url(_settings.CELERY_BROKER_URL)

        for info in datasets_info:
            event_payload = _json.dumps({
                "asset_type": "image",
                "object_key": info['name'],
                "bucket": getattr(_settings, 'TRAINING_BUCKET_NAME', 'mole-training-data'),
                "content_type": info.get('type', 'application/zip'),
                "source": "train_vision_async",
            })
            r.publish("mole:training:new_asset", event_payload)
            logger.info("train_vision_async | Evento publicado para: %s", info['name'])

        # Limpiar archivos locales tras la publicación exitosa
        for info in datasets_info:
            if os.path.exists(info['path']):
                os.remove(info['path'])

        return f"Vision training events published for {len(datasets_info)} dataset(s)"

    except _redis.RedisError as exc:
        logger.error("train_vision_async | Redis Pub/Sub falló: %s", exc)
        raise self.retry(exc=exc, countdown=5)
    except Exception:
        # Limpiar archivos en caso de error no recuperable
        for info in datasets_info:
            if os.path.exists(info['path']):
                os.remove(info['path'])
        raise