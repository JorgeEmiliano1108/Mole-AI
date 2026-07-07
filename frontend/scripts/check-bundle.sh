#!/bin/sh
# scripts/check-bundle.sh — CI: detecta chunks JS que superen 500 KB sin comprimir
set -euo pipefail

MAX_SIZE=512000  # 500 KB en bytes

# Excepciones documentadas: chunks que solo cargan en páginas específicas
# - echarts: ~1000 KB (solo admin.html, lazy load vía admin.js)
ALLOWLIST="echarts"

PASS=true

[ ! -d "dist/assets" ] && echo "FAIL: dist/assets/ no existe. Ejecuta 'pnpm build' primero." && exit 1

echo "=== Bundle size check (límite: 500 KB por chunk, excepto allowlist) ==="
echo ""

for f in dist/assets/*.js; do
  [ ! -f "$f" ] && continue
  size=$(stat --format=%s "$f" 2>/dev/null)
  name=$(basename "$f")
  size_kb=$((size / 1024))
  
  # Check allowlist
  allowed=false
  for a in $ALLOWLIST; do
    case "$name" in
      "$a-"*) allowed=true ;;
    esac
  done
  
  if [ "$size" -gt "$MAX_SIZE" ] && ! $allowed; then
    echo "❌  FAIL: $name = ${size_kb} KB (excede 500 KB)"
    PASS=false
  elif [ "$size" -gt "$MAX_SIZE" ] && $allowed; then
    echo "⚠️  ALLOWED: $name = ${size_kb} KB (en allowlist: solo admin.html)"
  else
    echo "✅  $name = ${size_kb} KB"
  fi
done

echo ""
if $PASS; then
  echo "PASS: Todos los chunks JS están dentro del límite (allowlist respetada)"
else
  echo "FAIL: Hay chunks que exceden 500 KB. Revisar manualChunks o lazy loading."
  exit 1
fi
