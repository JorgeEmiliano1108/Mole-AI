# ==========================================
# ETAPA 1: BUILDER (Descarga y Compilación)
# ==========================================
FROM python:3.11-slim as ms2_builder

ENV PIP_NO_CACHE_DIR=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /build

# Instalamos herramientas de sistema necesarias para compilar librerías de IA
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Creamos el entorno virtual
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copiamos solo los requirements primero (Aprovecha la caché de capas de Docker)
COPY requirements.txt .

# Instalamos las librerías en el entorno virtual
RUN pip install --upgrade pip setuptools wheel && \
    pip install -r requirements.txt

# ==========================================
# ETAPA 2: PRODUCCIÓN (Runtime Ligero)
# ==========================================
FROM python:3.11-slim as production

# Variables de entorno
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/opt/venv/bin:$PATH" \
    PYTHONPATH=/app \
    PORT=8002

WORKDIR /app

# Instalamos SOLO dependencias de ejecución (libgomp1 es vital para FAISS/PyTorch)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Copiamos el entorno virtual limpio desde el builder
COPY --from=ms2_builder /opt/venv /opt/venv

# Creamos usuario no-root por seguridad
RUN groupadd -r app && useradd -r -g app -m -d /home/app app

# Copiamos el código fuente de MS2
COPY . /app/ms2_rag_cag_service
RUN chown -R app:app /app

USER app
EXPOSE 8002

# CMD optimizado para Uvicorn/Gunicorn
CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "-w", "4", "-b", "0.0.0.0:8002", "ms2_rag_cag_service.app.main:app"]