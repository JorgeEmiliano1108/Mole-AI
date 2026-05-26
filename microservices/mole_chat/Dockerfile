# ==========================================
# ETAPA 1: BUILDER (Descarga y Compilación)
# ==========================================
FROM python:3.11-slim as builder

ENV PIP_NO_CACHE_DIR=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    wget \
    && rm -rf /var/lib/apt/lists/*

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install --upgrade pip setuptools wheel && \
    pip install -r requirements.txt

# ==========================================
# ETAPA 2: DESARROLLO (Hot-reload y dep. ejecución)
# ==========================================
FROM python:3.11-slim as development

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/opt/venv/bin:$PATH" \
    PYTHONPATH=/app \
    PORT=8002

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /opt/venv /opt/venv

EXPOSE 8002

# Hot-reload habilitado
CMD ["uvicorn", "app.api.main:app", "--host", "0.0.0.0", "--port", "8002", "--reload"]

# ==========================================
# ETAPA 3: PRODUCCIÓN (Runtime Ligero)
# ==========================================
FROM development as production

RUN groupadd -r app && useradd -r -g app -m -d /home/app app

COPY . /app

RUN chown -R app:app /app

# Crear directorio de logs con permisos correctos
RUN mkdir -p /app/logs && chown -R app:app /app/logs

USER app

# Uvicorn para mejor compatibilidad con lifespan events
CMD ["uvicorn", "app.api.main:app", "--host", "0.0.0.0", "--port", "8002", "--workers", "2"]