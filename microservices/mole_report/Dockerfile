# ==========================================
# ETAPA 1: BUILDER (Dependencias compiladas para WeasyPrint)
# ==========================================
FROM python:3.11-slim AS builder

ENV PIP_NO_CACHE_DIR=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libffi-dev \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# ==========================================
# ETAPA 2: DESARROLLO (WeasyPrint Runtime + Hot-reload)
# ==========================================
FROM python:3.11-slim AS development

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/opt/venv/bin:$PATH" \
    PYTHONPATH=/srv/ms3_reports \
    PORT=8003

WORKDIR /srv/ms3_reports

RUN apt-get update && apt-get install -y --no-install-recommends \
    libcairo2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf-xlib-2.0-0 \
    shared-mime-info \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /opt/venv /opt/venv

EXPOSE 8003

# Uvicorn con recarga (el worker se levantará por separado con el comando adaptado)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8003", "--reload"]

# ==========================================
# ETAPA 3: PRODUCCIÓN (Servicio final)
# ==========================================
FROM development AS production

RUN useradd --create-home --shell /bin/bash appuser && \
    chown -R appuser:appuser /srv/ms3_reports

COPY . .
RUN chown -R appuser:appuser /srv/ms3_reports

USER appuser

# Producción estandar
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8003"]