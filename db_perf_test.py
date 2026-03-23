import os
import sys
import time
import threading
import uuid
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mole_ai_backend.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.db import connection, transaction
from django.utils import timezone
from apps.core.infrastructure.repositories.models import SensorLog
from rest_framework.test import APIClient

User = get_user_model()

def test_endpoint(client, thread_id, results):
    start = time.time()
    response = client.get('/api/v1/admin/stats/', HTTP_HOST='localhost')
    end = time.time()
    duration = (end - start) * 1000  # ms
    results.append({
        'thread_id': thread_id,
        'status_code': response.status_code,
        'duration_ms': duration
    })

def main():
    print("--- INICIANDO TEST DE RENDIMIENTO DE BD ---")
    
    # 1. Clean previous test data to avoid accumulating too much
    print("[0] Limpiando base de datos (SensorLogs antiguos)...")
    initial_count = SensorLog.objects.count()
    if initial_count > 0:
        SensorLog.objects.all().delete()
        print(f"    Se eliminaron {initial_count} registros previos.")
    
    # 2. Ensure User EmiMole exists
    user, _ = User.objects.get_or_create(
        username='EmiMole', 
        defaults={'is_staff': True, 'is_superuser': True, 'email': 'emimole@mole.ai'}
    )
    
    client = APIClient()
    client.force_authenticate(user=user)

    # 3. Prepare data for insertion
    print("\n[1] Preparando 50,000 registros de prueba...")
    start_prep = time.time()
    plant_id = uuid.uuid4()
    now = timezone.now()
    
    logs = [
        SensorLog(
            plant_id=plant_id,
            recorded_at=now,
            soil_humidity=50.0 + (i % 10),
            air_temperature=25.0 + (i % 5),
            uv_index=5.0,
            ph_level=6.5
        ) for i in range(50000)
    ]
    print(f"Preparación completada en {time.time() - start_prep:.2f}s")
    
    results = []
    
    # 4. Starting the 10 concurrent requests
    print("\n[2] Iniciando inserción masiva y 10 peticiones concurrentes...")
    def run_concurrent_requests():
        threads = []
        for i in range(10):
            t = threading.Thread(target=test_endpoint, args=(client, i, results))
            threads.append(t)
            t.start()
        for t in threads:
            t.join()

    # Create thread for handling the requests
    req_thread = threading.Thread(target=run_concurrent_requests)
    
    start_total = time.time()
    req_thread.start()
    
    # 5. Bulk Create inside transaction
    start_insert = time.time()
    with transaction.atomic():
        SensorLog.objects.bulk_create(logs, batch_size=5000)
    end_insert = time.time()
    print(f"[+] Inserción masiva (50k) completada en: {end_insert - start_insert:.2f}s")
    
    req_thread.join()
    end_total = time.time()
    
    print(f"[+] Tiempo total del test: {end_total - start_total:.2f}s")
    
    print("\n[+] Resultados de las peticiones concurrentes al Dashboard:")
    for r in sorted(results, key=lambda x: x['thread_id']):
        print(f"    Thread {r['thread_id']:02d}: Status {r['status_code']} | Tiempo: {r['duration_ms']:.2f}ms")
        
    avg_req_time = sum(r['duration_ms'] for r in results) / len(results) if results else 0
    print(f"    => TIEMPO PROMEDIO DE RESPUESTA: {avg_req_time:.2f}ms")
    if avg_req_time < 300:
        print("    => [ÉXITO] El tiempo promedio se mantiene por debajo de 300ms.")
    else:
        print("    => [ALERTA] El tiempo promedio excedió los 300ms.")
        
    # 6. Check Deadlocks and Locks
    print("\n[3] Análisis de bloqueos (Deadlocks / Locks):")
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT count(*) 
            FROM pg_locks 
            WHERE NOT granted;
        """)
        row = cursor.fetchone()
        if row and row[0] > 0:
            print(f"    [!] Se detectaron {row[0]} bloqueos en espera (deadlocks/locks contention).")
        else:
            print("    [OK] No se detectaron bloqueos (deadlocks o esperas) en la base de datos.")
            
    # 7. Check DB Index Sizes
    print("\n[4] Análisis de tamaño de índices para `sensor_logs`:")
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT indexrelname, pg_size_pretty(pg_relation_size(indexrelid)) as index_size, pg_relation_size(indexrelid) as size_bytes
            FROM pg_stat_user_indexes 
            WHERE relname = 'sensor_logs';
        """)
        indexes = cursor.fetchall()
        
        total_index_bytes = 0
        for idx in indexes:
            print(f"    - Índice: {idx[0]} | Tamaño: {idx[1]}")
            total_index_bytes += idx[2]
            
        print(f"    => Tamaño total de índices en sensor_logs: {total_index_bytes / (1024*1024):.2f} MB")

if __name__ == '__main__':
    main()
