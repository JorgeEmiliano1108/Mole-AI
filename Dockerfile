FROM python:3.12-slim

LABEL maintainer="Mole AI Team"
LABEL description="Mole AI v2.0 - Diagnóstico de Plantas con Arquitectura Hexagonal"
LABEL version="2.0.0"
LABEL architecture="hexagonal_modular"

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    libpq-dev \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    wget \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copiar requirements actualizados
COPY requirements.txt .

# Instalar dependencias Python
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt && \
    rm -rf /root/.cache/pip

# Crear estructura de directorios
RUN mkdir -p /app/storage/images /app/storage/documents /app/storage/vectors /app/logs

# Copiar arquitectura hexagonal
COPY mole_ai/ /app/mole_ai/
# El main.py está dentro de mole_ai/

# Crear usuario non-root
RUN useradd -m -u 1000 moleai && \
    chown -R moleai:moleai /app && \
    chmod +x /app/storage /app/logs

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