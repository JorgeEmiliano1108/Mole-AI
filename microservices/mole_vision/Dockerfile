# ==========================================
# BASE: Dependencias de OS compartidas
# ==========================================
FROM python:3.11-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/opt/venv/bin:$PATH" \
    PYTHONPATH="/app"

WORKDIR /app

# Librerías en runtime para OpenCV y TFLite (Headless)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libjpeg62-turbo \
    libgomp1 \
    libstdc++6 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# ==========================================
# BUILDER: Compilación y dependencias
# ==========================================
FROM base AS builder

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    ca-certificates \
    curl \
    libjpeg-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

RUN python -m venv /opt/venv

COPY requirements.txt .

# Instalar dependencias Python
RUN pip install --upgrade pip setuptools wheel && \
    pip install -r requirements.txt

# ==========================================
# DESARROLLO (Hot-reload)
# ==========================================
FROM base AS development

# Copiamos solo el entorno virtual ya compilado
COPY --from=builder /opt/venv /opt/venv

EXPOSE 8001

CMD ["uvicorn", "app.api.main:app", "--host", "0.0.0.0", "--port", "8001", "--reload"]

# ==========================================
# 4. PRODUCCIÓN (Estática, Segura, Optimizada)
# ==========================================
FROM base AS production

RUN useradd --create-home --shell /bin/bash appuser

COPY --from=builder /opt/venv /opt/venv

# OPTIMIZACIÓN CRÍTICA: COPY --chown evita duplicar la capa en el historial
COPY --chown=appuser:appuser . /app

# Crear directorio de logs con permisos correctos
RUN mkdir -p /app/logs && chown -R appuser:appuser /app/logs

USER appuser
EXPOSE 8001

HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8001/api/v1/vision/health')" || exit 1

# Workers dinámicos o estáticos según orquestador
CMD ["uvicorn", "app.api.main:app", "--host", "0.0.0.0", "--port", "8001", "--workers", "1"]