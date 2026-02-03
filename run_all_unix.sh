#!/bin/bash
# Script para Unix/Linux/Mac - Levanta ambos servicios en entorno virtual

# Vision Service
echo "Iniciando Vision Service..."
cd ai_vision_service
if [ ! -d "venv" ]; then
  python3 -m venv venv
fi
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8001 &
cd ..

# RAG Service
echo "Iniciando RAG Service..."
cd ai_rag_service
if [ ! -d "venv" ]; then
  python3 -m venv venv
fi
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8002 &
cd ..

echo "Ambos servicios están levantándose en segundo plano."
