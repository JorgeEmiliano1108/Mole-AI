FROM python:3.11-slim
WORKDIR /srv/ms3_reports
COPY requirements.txt ./
# Install system libraries required by WeasyPrint (cairo/pango/gobject etc.)
RUN apt-get update && apt-get install -y \
	libcairo2 \
	libcairo2-dev \
	libpango-1.0-0 \
	libpangocairo-1.0-0 \
	libgdk-pixbuf-xlib-2.0-0 \
	libffi-dev \
	pkg-config \
	shared-mime-info \
	build-essential \
	&& rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir -r requirements.txt
COPY . .

# Create non-root user (M3: hardening)
RUN useradd --create-home --shell /bin/bash appuser \
    && chown -R appuser:appuser /srv/ms3_reports

# USER appuser

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8003"]
