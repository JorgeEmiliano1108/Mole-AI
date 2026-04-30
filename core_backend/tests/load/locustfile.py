# tests/load/locustfile.py
import os
import json
import uuid
import random
from datetime import datetime, timezone
from locust import HttpUser, task, between

class ESP32NodeUser(HttpUser):
    """
    Simula múltiples nodos ESP32 inyectando telemetría en el backend.
    Load Testing (Fase 4).
    """
    wait_time = between(1, 5)

    def on_start(self):
        # Leemos la llave segura desde las variables de entorno
        api_key = os.getenv('HARDWARE_API_KEY', 'TU_LLAVE_REAL_AQUI')
        
        # Simulamos los headers de HardwareAPIKey para el endpoint de ingesta
        self.headers = {
            "Content-Type": "application/json",
            "X-Hardware-Api-Key": api_key
        }
        self.plant_id = str(uuid.uuid4())

    @task
    def send_telemetry_batch(self):
        """
        Envía un payload estructurado según el SensorBatchSerializer.
        """
        payload = {
            "batch": [
                {
                    "plant_id": self.plant_id,
                    "recorded_at": datetime.now(timezone.utc).isoformat(),
                    "soil_humidity": random.uniform(20.0, 80.0),
                    "air_humidity": random.uniform(30.0, 90.0),
                    "air_temperature": random.uniform(15.0, 35.0),
                    "uv_index": random.uniform(0.0, 10.0),
                    "light_level": random.uniform(100.0, 10000.0),
                    "ph_level": random.uniform(5.5, 7.5)
                }
            ]
        }
        
        # Hacemos POST al endpoint de ingesta de batch
        with self.client.post(
            "/api/v1/sensor-data/batch/", 
            data=json.dumps(payload), 
            headers=self.headers, 
            catch_response=True
        ) as response:
            if response.status_code == 201:
                response.success()
            elif response.status_code == 401:
                response.failure("401 Unauthorized")
            else:
                response.failure(f"Falló con código: {response.status_code}. Respuesta: {response.text}")
