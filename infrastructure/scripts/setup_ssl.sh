#!/usr/bin/env bash
# =============================================================================
# Mole.AI — ISSUE-06: Certbot SSL + Host-Level Nginx (SRE Version)
# =============================================================================
set -euo pipefail

# ── Cargar variables del .env ────────────────────────────────────────────────
if [ ! -f ".env" ]; then
    echo "❌ Error: Archivo .env no encontrado en este directorio."
    exit 1
fi

export $(grep -v '^#' .env | xargs)

if [ -z "${DOMAIN:-}" ] || [ -z "${SSL_EMAIL:-}" ]; then
    echo "❌ Error: Las variables DOMAIN y SSL_EMAIL deben estar definidas en el .env"
    exit 1
fi

echo "═══════════════════════════════════════════════════════════════"
echo " MOLE.AI — Provisionando SSL para: ${DOMAIN}"
echo "═══════════════════════════════════════════════════════════════"

echo "[1/7] Instalando Nginx..."
sudo apt-get update -y
sudo apt-get install -y nginx

echo "[2/7] Instalando Certbot..."
sudo apt-get install -y snapd
sudo snap install core 2>/dev/null || true
sudo snap refresh core
sudo snap install --classic certbot
sudo ln -sf /snap/bin/certbot /usr/bin/certbot

echo "[3/7] Creando directorio ACME challenge..."
sudo mkdir -p /var/www/certbot

echo "[4/7] Desplegando configuración temporal HTTP..."
sudo rm -f /etc/nginx/sites-enabled/default

# Se usa un bloque estático y luego reemplazaremos el dominio con 'sed'
sudo tee /etc/nginx/sites-available/mole_ai > /dev/null << 'NGINX_TEMP'
server {
    listen 80;
    listen [::]:80;
    server_name ___DOMAIN___ www.___DOMAIN___;

    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
NGINX_TEMP

# Reemplazo seguro de variables
sudo sed -i "s/___DOMAIN___/${DOMAIN}/g" /etc/nginx/sites-available/mole_ai
sudo ln -sf /etc/nginx/sites-available/mole_ai /etc/nginx/sites-enabled/mole_ai

echo "[5/7] Probando e iniciando Nginx..."
sudo nginx -t
sudo systemctl enable nginx
sudo systemctl restart nginx

echo "[6/7] Obteniendo Certificado SSL con Certbot..."
sudo certbot certonly \
    --webroot \
    --webroot-path /var/www/certbot \
    -d ${DOMAIN} \
    -d www.${DOMAIN} \
    --email ${SSL_EMAIL} \
    --agree-tos \
    --non-interactive

echo "[7/7] Desplegando configuración SSL completa..."
sudo tee /etc/nginx/sites-available/mole_ai > /dev/null << 'NGINX_FULL'
map $http_upgrade $connection_upgrade {
    default upgrade;
    ''      close;
}

server {
    listen 80;
    listen [::]:80;
    server_name ___DOMAIN___ www.___DOMAIN___;

    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    location / {
        return 301 https://$host$request_uri;
    }
}

server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name ___DOMAIN___ www.___DOMAIN___;

    ssl_certificate     /etc/letsencrypt/live/___DOMAIN___/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/___DOMAIN___/privkey.pem;

    ssl_protocols       TLSv1.2 TLSv1.3;
    ssl_ciphers         ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers on;
    ssl_session_tickets off;

    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;

    client_max_body_size 20M;

    location / {
        proxy_pass         http://127.0.0.1:8080;
        proxy_set_header   Host              $host;
        proxy_set_header   X-Real-IP         $remote_addr;
        proxy_set_header   X-Forwarded-For   $proxy_add_x_forwarded_for;
        proxy_set_header   X-Forwarded-Proto https;
        proxy_http_version 1.1;
        proxy_set_header   Upgrade    $http_upgrade;
        proxy_set_header   Connection $connection_upgrade;
    }

    location /ws/edge/ {
        proxy_pass         http://127.0.0.1:18789;
        proxy_http_version 1.1;
        proxy_set_header   Upgrade    $http_upgrade;
        proxy_set_header   Connection "upgrade";
        proxy_set_header   Host       $host;
        proxy_set_header   X-Real-IP  $remote_addr;
        proxy_set_header   X-Forwarded-For   $proxy_add_x_forwarded_for;
        proxy_set_header   X-Forwarded-Proto https;
        proxy_read_timeout 86400;
    }
}
NGINX_FULL

# Reemplazo final
sudo sed -i "s/___DOMAIN___/${DOMAIN}/g" /etc/nginx/sites-available/mole_ai

sudo nginx -t
sudo systemctl reload nginx
sudo systemctl enable certbot.timer

echo "✅ Listo! Navega a https://${DOMAIN}"