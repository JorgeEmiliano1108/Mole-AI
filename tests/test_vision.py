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
import requests
import json


url = "http://localhost:8001/api/v1/mole-ai/chat"
# Una imagen de prueba (Manzanilla)
image_url = "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c8/Matricaria_chamomilla.jpg/640px-Matricaria_chamomilla.jpg"

payload = {
    "message": "¿Qué planta es esta y para qué sirve medicinalmente?",
    "image": image_url,  # Aquí enviamos la URL
    "history": []
}

headers = {"Content-Type": "application/json"}

print(f"📡 Enviando imagen a Mole-AI ({payload['image']})...")

try:
    response = requests.post(url, json=payload, headers=headers)
    
    if response.status_code == 200:
        print("\n✅ RESPUESTA VISUAL RECIBIDA:")
        print("------------------------------------------------")
        print(response.json()) # O response.json()['response'] según tu esquema
        print("------------------------------------------------")
    else:
        print(f"\n❌ Error {response.status_code}: {response.text}")

except Exception as e:
    print(f"\n❌ Error de conexión: {e}")