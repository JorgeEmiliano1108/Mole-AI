# ==========================================
# ETAPA 1: BUILDER (Dependencias de sistema pesadas)
# ==========================================
FROM python:3.11-slim as builder

ENV PIP_NO_CACHE_DIR=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    ca-certificates \
    curl \
    libjpeg-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install --upgrade pip setuptools wheel && \
    pip install -r requirements.txt

# ==========================================
# ETAPA 2: DESARROLLO (Hot-reload, dependencias ligeras)
# ==========================================
FROM python:3.11-slim as development

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/opt/venv/bin:$PATH" \
    PYTHONPATH=/app

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libjpeg62-turbo \
    libgomp1 \
    libstdc++6 \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /opt/venv /opt/venv

EXPOSE 8001

# Hot reload para desarrollo (el código se monta como volumen en compose)
CMD ["uvicorn", "ms1_vision.app.main:app", "--host", "0.0.0.0", "--port", "8001", "--reload"]

# ==========================================
# ETAPA 3: PRODUCCIÓN (Estática, Segura)
# ==========================================
FROM development as production

RUN useradd --create-home --shell /bin/bash appuser

# En producción empaquetamos el código
COPY . /app/ms1_vision
RUN chown -R appuser:appuser /app

USER appuser

# Sin reload para eficiencia
CMD ["uvicorn", "ms1_vision.app.main:app", "--host", "0.0.0.0", "--port", "8001", "--workers", "1"]
