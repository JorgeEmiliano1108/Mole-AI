#!/bin/bash
# Orquestador de pruebas de sistema end-to-end.
# Servicios: ms2_chat, ms1_vision, ms3_reports + PostgreSQL, Redis, MinIO, fake NIM
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

echo "═══════════════════════════════════════════════════"
echo "  Mole-AI System Tests — End to End"
echo "═══════════════════════════════════════════════════"
echo ""

COMPOSE_FILE="infrastructure/docker-compose.e2e.yml"

# ── 1. Levantar entorno ───────────────────────────────────────
echo "=== [1/4] Levantando entorno Docker ==="
cd "$ROOT_DIR"
docker compose -f "$COMPOSE_FILE" up -d --remove-orphans
echo ""

# ── 2. Esperar servicios ──────────────────────────────────────
echo "=== [2/4] Esperando servicios (health checks) ==="
bash scripts/wait-for-services.sh
echo ""

# ── 3. Ejecutar pruebas ───────────────────────────────────────
echo "=== [3/4] Ejecutando pruebas de sistema ==="
TEST_RESULT=0
for test in tests/system/test_*.sh; do
    echo ""
    echo "───────────────────────────────────────────"
    echo "▶️  Ejecutando $(basename "$test")"
    echo "───────────────────────────────────────────"
    if bash "$test"; then
        echo "  ✅ $(basename "$test") PASSED"
    else
        echo "  ❌ $(basename "$test") FAILED"
        TEST_RESULT=1
    fi
done
echo ""

# ── 4. Limpiar ────────────────────────────────────────────────
echo "=== [4/4] Limpiando entorno ==="
docker compose -f "$COMPOSE_FILE" down -v
echo ""

echo "═══════════════════════════════════════════════════"
if [ "$TEST_RESULT" -eq 0 ]; then
    echo "  ✅ TODAS LAS PRUEBAS PASARON"
else
    echo "  ❌ ALGUNA PRUEBA FALLÓ (revisar logs arriba)"
fi
echo "═══════════════════════════════════════════════════"
exit "$TEST_RESULT"
