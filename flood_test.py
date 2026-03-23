import os
import sys
import time
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

print("\n--- INICIANDO INUNDACIÓN DE TASKS (QUEUE FLOODING) ---")

def trigger_report(i):
    start = time.time()
    res = client.post('/api/v1/reports/master/', HTTP_HOST='localhost')
    if res.status_code == 200:
        return res.data.get('job_id'), time.time() - start
    print(f"Error {res.status_code}: {res.content}")
    return None, time.time() - start

# Disparar 20 peticiones simultáneas
job_ids = []
start_flood = time.time()
with ThreadPoolExecutor(max_workers=20) as executor:
    futures = [executor.submit(trigger_report, i) for i in range(20)]
    for f in futures:
        jid, duration = f.result()
        if jid:
            job_ids.append(jid)
end_flood = time.time()

print(f"[{end_flood - start_flood:.2f}s] Se obtuvieron {len(job_ids)} Job IDs.")

print("\n--- CICLO DE VIDA DEL JOB ID (POLLING) ---")
# Monitor the status of each job ID
completed = set()
times = {}
start_poll = time.time()

while len(completed) < len(job_ids):
    for jid in job_ids:
        if jid in completed:
            continue
        res = client.get(f'/api/v1/reports/master/status/{jid}/', HTTP_HOST='localhost')
    if res.status_code == 200:
            status = res.data.get('status')
            if status == 'completed':
                completed.add(jid)
                times[jid] = time.time() - start_poll
                print(f"[+] Task {jid} -> {status} (Archivo: {res.data.get('file_url')})")
            elif status == 'failed':
                completed.add(jid)
                print(f"[-] Task {jid} -> FAILED")
            else:
                pass # processing
    time.sleep(0.5)
    if time.time() - start_poll > 30:
        print("[!] Timeout esperando tareas.")
        break

avg_time = sum(times.values()) / len(times) if times else 0
print(f"\n=> Tiempo promedio desde petición hasta archivo listo: {avg_time:.2f}s")
