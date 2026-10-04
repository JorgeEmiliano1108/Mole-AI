#!/usr/bin/env bash
# =============================================================================
# check-mobile-contract.sh — Gate del contrato móvil (issue 11)
#
# Regenera el schema OpenAPI con las env de test y lo compara contra el
# snapshot versionado docs/contracts/openapi.yml.
# Falla (exit 1) con diff no vacío: todo cambio de paths/métodos debe
# declararse en .scratch/mvp-flutter/issues/11-contrato-movil-congelado.md
# y reflejarse en docs/mobile-contract.md antes de merge.
#
# Uso local:  bash scripts/check-mobile-contract.sh
# Requiere:   venv con requirements de core_backend (ver AGENTS.md).
# =============================================================================
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SNAPSHOT="$ROOT/docs/contracts/openapi.yml"
PY="${PY:-/tmp/opencode/venvs/core/bin/python}"
TMP_SCHEMA="$(mktemp /tmp/openapi-check.XXXXXX.yml)"

cleanup() { rm -f "$TMP_SCHEMA"; }
trap cleanup EXIT

if [ ! -f "$SNAPSHOT" ]; then
    echo "[FAIL] No existe snapshot: docs/contracts/openapi.yml"
    exit 1
fi

echo "== check-mobile-contract: regenerando schema =="
mkdir -p /tmp/opencode
(
    cd "$ROOT"
    env DEBUG=True SECRET_KEY=test JWT_SECRET_KEY=test HARDWARE_API_KEY=test \
        DJANGO_LTK_ENCRYPTION_KEY=kCF3lDElvKqx5JycjjC8Kn9NRoVsy0gkhHqk6yAXhIk= \
        DB_URL=sqlite:////tmp/opencode/schema-check.sqlite3 \
        "$PY" core_backend/manage.py spectacular --file "$TMP_SCHEMA" 2>/dev/null
)

# Gate ESTRUCTURAL (no cosmético): compara paths/métodos/operationId/
# parámetros/códigos ignorando description/summary/tags. Las descripciones a
# mano del snapshot se preservan intactas — jamás se regenera el archivo.
# Requiere PyYAML en el Python que corre el gate (venv de core_backend la trae).
"$PY" "$ROOT/scripts/canonical-openapi.py" "$TMP_SCHEMA" "$SNAPSHOT"
STATUS=$?
if [ $STATUS -ne 0 ]; then
    echo "-------------------------------------"
    echo "Actualiza docs/contracts/openapi.yml a mano (descripciones intactas)"
    echo "+ docs/mobile-contract.md y documenta el cambio en"
    echo "issues/11-contrato-movil-congelado.md"
    exit 1
fi
