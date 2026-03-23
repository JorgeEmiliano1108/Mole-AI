from celery import shared_task
from celery.exceptions import Retry, MaxRetriesExceededError
import requests
import os

@shared_task(bind=True, max_retries=3, name="train_rag_async")
def train_rag_async(self, file_path, original_filename, content_type):
    try:
        with open(file_path, 'rb') as f:
            file_data = f.read()
        files = {'file': (original_filename, file_data, content_type)}
        response = requests.post("http://fastapi_rag:8002/api/v1/train/", files=files, timeout=30)
        response.raise_for_status()
        
        # Bloque de éxito: limpiar archivo
        if os.path.exists(file_path):
            os.remove(file_path)
            
        return "RAG Training started successfully"
    except requests.exceptions.ConnectionError as exc:
        try:
            # NO borrar archivo, sólo reintentar
            raise self.retry(exc=exc, countdown=2)
        except MaxRetriesExceededError:
            # SÓLO AHÍ borrar el archivo en caso de fallo definitivo
            if os.path.exists(file_path):
                os.remove(file_path)
            raise
    except Retry:
        raise
    except Exception:
        # Fallo de otro tipo, limpiar
        if os.path.exists(file_path):
            os.remove(file_path)
        raise

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
            
        response = requests.post("http://fastapi_vision:8001/api/v1/train/", files=files, timeout=30)
        
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
    except Retry:
        raise
    except Exception:
        for f in file_objs:
            f.close()
        for info in datasets_info:
            if os.path.exists(info['path']):
                os.remove(info['path'])
        raise

@shared_task(bind=True, max_retries=3, name="analyze_vision_async")
def analyze_vision_async(self, file_path, original_filename, content_type):
    try:
        with open(file_path, 'rb') as f:
            file_data = f.read()
        
        # El endpoint de MS1 espera un 'file'
        files = {'file': (original_filename, file_data, content_type)}
        response = requests.post("http://fastapi_vision:8001/api/v1/vision/analyze", files=files, timeout=30)
        response.raise_for_status()
        
        # Éxito: limpiar
        if os.path.exists(file_path):
            os.remove(file_path)
            
        return response.json()
    except requests.exceptions.ConnectionError as exc:
        try:
            raise self.retry(exc=exc, countdown=2)
        except MaxRetriesExceededError:
            if os.path.exists(file_path):
                os.remove(file_path)
            raise
    except Retry:
        raise
    except Exception:
        if os.path.exists(file_path):
            os.remove(file_path)
        raise
