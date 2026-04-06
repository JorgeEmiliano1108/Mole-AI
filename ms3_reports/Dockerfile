# ==========================================
# ETAPA 1: DEPENDENCIAS C (Builder Stage)
# ==========================================
FROM python:3.11-slim as ms3_builder

ENV PIP_NO_CACHE_DIR=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /build

# Instalamos herramientas de compilación necesarias para WeasyPrint y Cffi
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libffi-dev \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Crear entorno virtual
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# ==========================================
# ETAPA 2: PRODUCCIÓN (Runtime Stage)
# ==========================================
FROM python:3.11-slim as production

# Variables de entorno para ejecución
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/opt/venv/bin:$PATH" \
    WORKDIR=/srv/ms3_reports

WORKDIR $WORKDIR

# Instalamos SOLO las librerías compartidas de ejecución para WeasyPrint
# Eliminamos build-essential y archivos dev que ya no sirven
# CORRECCIÓN: Usamos el nombre actualizado libgdk-pixbuf-xlib-2.0-0
RUN apt-get update && apt-get install -y --no-install-recommends \
    libcairo2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf-xlib-2.0-0 \
    shared-mime-info \
    && rm -rf /var/lib/apt/lists/*

# Copiamos el entorno virtual ya cocinado desde ms3_builder
COPY --from=ms3_builder /opt/venv /opt/venv

# Creamos usuario de seguridad
RUN useradd --create-home --shell /bin/bash appuser && \
    chown -R appuser:appuser $WORKDIR

# Copiamos el código (Esto se usará en producción)
COPY . .
RUN chown -R appuser:appuser $WORKDIR

USER appuser
EXPOSE 8003

# Dejamos el usuario listo pero el CMD lo definiremos en el compose para flexibilidad
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8003"]