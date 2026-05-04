# ==========================================
# BASE: Dependencias de OS compartidas
# ==========================================
FROM python:3.11-slim as base

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
FROM base as builder

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
FROM base as development

# Copiamos solo el entorno virtual ya compilado
COPY --from=builder /opt/venv /opt/venv

EXPOSE 8001

CMD ["uvicorn", "app.api.main:app", "--host", "0.0.0.0", "--port", "8001", "--reload"]

# ==========================================
# 4. PRODUCCIÓN (Estática, Segura, Optimizada)
# ==========================================
FROM base as production

RUN useradd --create-home --shell /bin/bash appuser

COPY --from=builder /opt/venv /opt/venv

# OPTIMIZACIÓN CRÍTICA: COPY --chown evita duplicar la capa en el historial
COPY --chown=appuser:appuser . /app

USER appuser
EXPOSE 8001

# Workers dinámicos o estáticos según orquestador
CMD ["uvicorn", "app.api.main:app", "--host", "0.0.0.0", "--port", "8001", "--workers", "1"]