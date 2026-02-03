FROM python:3.12-slim

LABEL maintainer="Mole AI Team"
LABEL description="Mole AI v2.0 - Diagnóstico de Plantas con Phi-3.5 Vision-Instruct Q4"
LABEL version="2.0.0"
LABEL model="phi-3.5-vision-instruct-q4"

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    API_HOST=0.0.0.0 \
    API_PORT=8000 \
    LOG_LEVEL=INFO

WORKDIR /app

# Instalar dependencias del sistema (optimizadas para Phi-3.5 + CPU inference)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    libpq-dev \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/* && apt-get clean

# Copiar requirements
COPY requirements.txt .

# Instalar dependencias Python (con optimizaciones)
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# Crear estructura de directorios
RUN mkdir -p \
    storage/vectors \
    storage/uploads \
    storage/documents \
    logs

# Copiar aplicación FastAPI + RAG + Phi-3.5
COPY mole_ai/ ./mole_ai/
COPY .env.example .env

# Crear usuario non-root
RUN useradd -m -u 1000 moleai && \
    chown -R moleai:moleai /app

USER moleai

# Health check
HEALTHCHECK --interval=10s --timeout=30s --start-period=60s --retries=5 \
    CMD curl -f http://localhost:8000/health || exit 1

EXPOSE 8000

# CMD con uvicorn
CMD ["python", "-m", "uvicorn", "mole_ai.main:app", \
     "--host", "0.0.0.0", "--port", "8000", "--log-level", "info"]

# Exponer puerto
EXPOSE 8000

# Variables de entorno
ENV MODEL_NAME="microsoft/Phi-3.5-vision-instruct"
ENV EMBEDDING_MODEL="sentence-transformers/all-MiniLM-L6-v2"
ENV USE_LOCAL_OLLAMA="false"
ENV OLLAMA_URL="http://localhost:11434"
ENV POSTGRES_HOST="postgres"
ENV POSTGRES_PORT="5432"
ENV POSTGRES_DB="mole_ai_db"
ENV POSTGRES_USER="mole_user"
ENV POSTGRES_PASSWORD="mole_pass_2026"
ENV VECTOR_DB_PATH="/app/storage/vectors"
ENV DOCUMENT_STORAGE_PATH="/app/storage/documents"
ENV USE_CHROMA="false"
ENV DEBUG="false"
ENV LOG_LEVEL="info"
ENV API_PORT="8000"

# Health check mejorado
HEALTHCHECK --interval=30s --timeout=10s --start-period=300s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Cambiar a usuario non-root
USER moleai

# Comando de ejecución
CMD ["python", "-m", "mole_ai.main"]