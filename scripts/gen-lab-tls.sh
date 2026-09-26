#!/usr/bin/env bash
# gen-lab-tls.sh — CA + certificado de laboratorio para nginx 443 (issue B-03).
# Uso:  SAN_IP=98.12.2.179 ./scripts/gen-lab-tls.sh
# Idempotente: reutiliza la CA existente; regenera solo el cert de servidor.
#   - infrastructure/nginx/certs/: ca.key (gitignored), ca.crt, server.key/crt (gitignored)
#   - microservices/esp32_node/main/certs/lab_ca.pem: ancla pública (versionada)
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CERTD="$ROOT/infrastructure/nginx/certs"
FWD="$ROOT/microservices/esp32_node/main/certs"
SAN_IP="${SAN_IP:-127.0.0.1}"
mkdir -p "$CERTD" "$FWD"

if [ ! -f "$CERTD/ca.key" ]; then
    openssl req -x509 -newkey rsa:2048 -nodes -days 825 \
        -keyout "$CERTD/ca.key" -out "$CERTD/ca.crt" \
        -subj "/CN=MoleAI-Lab-CA" 2>/dev/null
    echo "CA creada"
fi

openssl req -newkey rsa:2048 -nodes -keyout "$CERTD/server.key" \
    -out "$CERTD/server.csr" -subj "/CN=mole-edge.local" 2>/dev/null
printf "subjectAltName=DNS:mole-edge.local,DNS:localhost,IP:127.0.0.1,IP:%s\n" "$SAN_IP" \
    > "$CERTD/server.ext"
openssl x509 -req -in "$CERTD/server.csr" -CA "$CERTD/ca.crt" -CAkey "$CERTD/ca.key" \
    -CAcreateserial -days 825 -extfile "$CERTD/server.ext" \
    -out "$CERTD/server.crt" 2>/dev/null
rm -f "$CERTD/server.csr" "$CERTD/server.ext" "$CERTD/ca.srl"
cp "$CERTD/ca.crt" "$FWD/lab_ca.pem"
chmod 600 "$CERTD/ca.key" "$CERTD/server.key"
echo "OK: server.crt (SAN IP=$SAN_IP) + lab_ca.pem sincronizado"
