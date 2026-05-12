# -------------------------------------------------
# 1️⃣ Builder – compila dependencias pesadas
# -------------------------------------------------
FROM python:3.11-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PATH="/opt/venv/bin:$PATH"

WORKDIR /build

# Herramientas de compilación (solo en builder)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev && \
    rm -rf /var/lib/apt/lists/*

# Entorno virtual aislado
RUN python -m venv /opt/venv

COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# -------------------------------------------------
# 2️⃣ Runtime – capa mínima de ejecución
# -------------------------------------------------
FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH"

WORKDIR /app

# Cliente PostgreSQL ligero y curl para healthcheck
RUN apt-get update && \
    apt-get install -y --no-install-recommends libpq5 curl && \
    rm -rf /var/lib/apt/lists/*

# Copia venv compilado
COPY --from=builder /opt/venv /opt/venv

# Crear usuario
RUN useradd --create-home --shell /bin/bash appuser

# Copiar código fuente y entrypoint (como root)
WORKDIR /app
COPY . /app/

# Dar permisos ANTES de cambiar de usuario
RUN chown -R appuser:appuser /app && chmod +x /app/entrypoint.sh

# Cambiar a usuario sin privilegios al final
USER appuser

EXPOSE 8000
HEALTHCHECK --interval=5s --timeout=3s --retries=5 \
    CMD ["curl", "-f", "http://127.0.0.1:8000/health/"] || exit 1
ENTRYPOINT ["/app/entrypoint.sh"]