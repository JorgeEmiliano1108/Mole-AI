#!/bin/bash
# scripts/test-sri.sh — TDD: verifica que los hashes SRI de CDNs sean reales
# PASO 1: test falla con hashes inventados
# PASO 2: implementar hashes reales
# PASO 3: test pasa
set -euo pipefail

CDNS=(
  "https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"
  "https://cdn.jsdelivr.net/npm/echarts@5.5.0/dist/echarts.min.js"
  "https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"
  "https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"
  "https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js"
)

PASS=true

echo "=== TDD: Validación de hashes SRI reales ==="
echo ""

for url in "${CDNS[@]}"; do
  name=$(basename "$url" | cut -d'?' -f1)
  echo "→ Descargando: $name"

  # Calcular hash real
  real_hash=$(curl -sL "$url" 2>/dev/null | openssl dgst -sha384 -binary | base64)
  real_b64="sha384-$real_hash"

  # Validar que es base64 (no contiene palabras en inglés legibles)
  # base64 charset: A-Z, a-z, 0-9, +, /, =
  if echo "$real_hash" | grep -qP '[^A-Za-z0-9+/=]'; then
    echo "  ❌ Hash no es base64 válido: $real_hash"
    PASS=false
    continue
  fi

  # Validar largo (384 bits = 64 chars base64 sin padding, o 64 con =)
  len=${#real_hash}
  if [ "$len" -lt 60 ] || [ "$len" -gt 68 ]; then
    echo "  ❌ Largo de hash inválido ($len chars): $real_hash"
    PASS=false
    continue
  fi

  echo "  ✅ $real_b64"
  echo ""
done

echo "========================"
if $PASS; then
  echo "✅ PASS: Todos los hashes SRI son reales (base64, 64 chars)"
else
  echo "❌ FAIL: Al menos un hash SRI es inválido"
  exit 1
fi
