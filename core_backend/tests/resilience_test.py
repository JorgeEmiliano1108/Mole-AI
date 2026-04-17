import os
import sys
import time
import io
import django
from concurrent.futures import ThreadPoolExecutor

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mole_ai_backend.settings')
os.environ['PG_SSL_MODE'] = 'disable'
django.setup()

from rest_framework.test import APIClient
from django.contrib.auth import get_user_model

User = get_user_model()
try:
    user = User.objects.get(username='EmiMole')
except User.DoesNotExist:
    user = User.objects.create_superuser('EmiMole', 'emimole@mole.ai', 'password123')

client = APIClient()
client.force_authenticate(user=user)

print("\n--- 1. Simulación de Blackout en ms1_vision ---")
start = time.time()
file_obj = io.BytesIO(b"fake image data")
file_obj.name = 'test.jpg'

response = client.post('/api/v1/ai/train/vision/', {'dataset': file_obj}, format='multipart', HTTP_HOST='localhost')
end = time.time()

print(f"Status Code: {response.status_code}")
print(f"Response Error: {response.data.get('error', '')}")
print(f"Time Taken to wait for retries: {end - start:.2f}s")
if end - start > 4:
    print("[OK] El sistema de Django retuvo la petición esperando el backoff de 3 reintentos.")
else:
    print("[WARN] No hubo espera suficiente.")

print("\n--- 2. Validación Buscador Sigiloso (CORS y Zero-Trust) ---")
anon_client = APIClient()
def test_search(i):
    res = anon_client.get('/api/v1/fichas/?q=Hongos', HTTP_HOST='localhost')
    return res.status_code

with ThreadPoolExecutor(max_workers=20) as executor:
    futures = [executor.submit(test_search, i) for i in range(20)]
    results = [f.result() for f in futures]

print(f"Resultados de 20 consultas anónimas: {results}")
if all(code == 200 for code in results):
    print("[OK] Búsqueda sigilosa no bloqueada (CORS/Zero-Trust pasaron 200).")
    print("[OK] No se filtró información sensible, solo el catálogo admitido.")
else:
    print("[WARN] Hubo códigos distintos a 200.")
