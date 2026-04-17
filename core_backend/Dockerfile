# ==========================================
# ETAPA 1: BUILDER (La máquina pesada)
# ==========================================
FROM python:3.11-slim as builder

ENV PIP_NO_CACHE_DIR=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /build

# Instalamos compiladores pesados (se quedarán en esta etapa)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Creamos un entorno virtual para aislar las librerías
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# ==========================================
# ETAPA 2: DESARROLLO (Para tu Docker Compose)
# ==========================================
FROM python:3.11-slim as development

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/opt/venv/bin:$PATH"

WORKDIR /app

# Solo instalamos la librería de ejecución de Postgres (súper ligera)
RUN apt-get update && \
    apt-get install -y --no-install-recommends libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Copiamos las librerías ya compiladas desde el builder
COPY --from=builder /opt/venv /opt/venv

RUN useradd --create-home --shell /bin/bash appuser

# En desarrollo, el código se monta por volumen, pero preparamos el entrypoint
COPY entrypoint.sh /app/
RUN chmod +x /app/entrypoint.sh && chown -R appuser:appuser /app

USER appuser
EXPOSE 8000
ENTRYPOINT ["/app/entrypoint.sh"]

# ==========================================
# ETAPA 3: PRODUCCIÓN (La imagen final sellada)
# ==========================================
FROM development as production

USER root
# En producción, no hay volúmenes, copiamos el código final
COPY . /app/
RUN chown -R appuser:appuser /app
USER appuser

# Listo para despliegue