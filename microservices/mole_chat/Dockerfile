# ==========================================
# ETAPA 1: BUILDER
# ==========================================
FROM python:3.11-slim AS builder

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

COPY requirements.lock .
RUN pip install --upgrade pip setuptools wheel && \
    pip install -r requirements.lock

# ==========================================
# ETAPA 2: BASE (minimal runtime deps)
# ==========================================
FROM python:3.11-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/opt/venv/bin:$PATH" \
    PYTHONPATH=/app \
    PORT=8002

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/* \
    && addgroup --system --gid 1001 appgroup \
    && adduser --system --uid 1001 --ingroup appgroup --home /home/app --shell /bin/false appuser

COPY --from=builder /opt/venv /opt/venv

EXPOSE 8002

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8002/api/v1/health')" || exit 1

# ==========================================
# ETAPA 3: PRODUCCIÓN (runtime mínimo)
# ==========================================
FROM base AS development

CMD ["uvicorn", "app.api.main:app", "--host", "0.0.0.0", "--port", "8002", "--reload"]

# ==========================================
# ETAPA 4: PRODUCCIÓN (runtime mínimo)
# ==========================================
FROM base AS production

COPY --chown=appuser:appgroup app/ /app/app/
COPY --chown=appuser:appgroup prompts/ /app/prompts/

RUN mkdir -p /app/logs && chown -R appuser:appgroup /app/logs

USER appuser

# Remove shell access and SUID binaries
RUN find / -perm /6000 -type f -exec chmod a-s {} \; 2>/dev/null || true

CMD ["uvicorn", "app.api.main:app", "--host", "0.0.0.0", "--port", "8002", "--workers", "2"]
