#!/usr/bin/env python3
"""
Mole.AI - Automated Database Stress Testing Script
Objetivo: Bombardeo concurrente de telemetría para evaluar Deadlocks 
y contención en locks The PostgreSQL row-level.
Uso: Ejecutar localmente contra el contenedor django_backend
"""

import requests
import concurrent.futures
import time
import uuid

# Reemplaza con una IP/Puerto accesible a Django host-side o docker dns
BASE_URL = "http://localhost:8000/api/v1"
CONCURRENT_REQUESTS = 100

def send_telemetry_payload(idx):
    payload = {
        "username": f"stress_usr_{idx}_{uuid.uuid4().hex[:6]}",
        "password": "StrongPassword123!",
        "email": f"tester_{idx}_{uuid.uuid4().hex[:6]}@mole.ai"
    }
    
    try:
        headers = {"Content-Type": "application/json"}
        resp = requests.post(f"{BASE_URL}/auth/register/", json=payload, headers=headers, timeout=20)
        return resp.status_code, resp.json() if resp.status_code in [200, 201] else resp.text
    except Exception as e:
        return 500, str(e)

def format_results(results):
    codes = {}
    for code, _ in results:
        codes[code] = codes.get(code, 0) + 1
    return codes

if __name__ == "__main__":
    print(f"============================================================")
    print(f" MOLE.AI STRESS TESTING SUITE: DEADLOCK SIMULATION ")
    print(f" Tirando {CONCURRENT_REQUESTS} peticiones en un solo milisegundo...")
    print(f"============================================================")
    
    start_time = time.time()
    
    # max_workers = 100 asegura que la contención sea masiva y asíncrona
    with concurrent.futures.ThreadPoolExecutor(max_workers=CONCURRENT_REQUESTS) as executor:
        futures = [executor.submit(send_telemetry_payload, i) for i in range(CONCURRENT_REQUESTS)]
        
        results = []
        for future in concurrent.futures.as_completed(futures):
            results.append(future.result())

    end_time = time.time()
    
    codes = format_results(results)
    
    print("\n--- Resultados ---")
    print(f"Duración de la contienda: {end_time - start_time:.2f} segundos")
    for status_code, count in codes.items():
        print(f"HTTP Status {status_code}: {count} peticiones")
        
    if 500 in codes or 503 in codes:
        print("\n[!] DETECCIÓN DE CONCURRENCIA FALLIDA (Posibles Deadlocks o Timeout en PG).")
        # Mostrar un ejemplar del error
        for r in results:
            if r[0] in [500, 503]:
                print(f"Sample Error: {r[1]}")
                break
    else:
        print("\n[\u2713] LA BASE DE DATOS SOPORTÓ EL BOMBARDEO SIN DEADLOCKS.")
