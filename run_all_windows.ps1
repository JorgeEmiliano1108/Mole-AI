# Script para Windows PowerShell - Levanta ambos servicios en entorno virtual

# Vision Service
Write-Host "Iniciando Vision Service..."
Start-Process powershell -ArgumentList @'-NoExit', '-Command', "cd ai_vision_service; if (!(Test-Path venv)) { python -m venv venv }; .\venv\Scripts\Activate.ps1; pip install -r requirements.txt; uvicorn main:app --reload --port 8001"

# RAG Service
Write-Host "Iniciando RAG Service..."
Start-Process powershell -ArgumentList @'-NoExit', '-Command', "cd ai_rag_service; if (!(Test-Path venv)) { python -m venv venv }; .\venv\Scripts\Activate.ps1; pip install -r requirements.txt; uvicorn main:app --reload --port 8002"

Write-Host "Ambos servicios están levantándose en terminales separadas."
