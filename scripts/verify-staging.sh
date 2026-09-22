#!/usr/bin/env bash
# =============================================================================
# verify-staging.sh — Verificación de entorno contra un backend vivo (V2).
#
# Uso:  BASE_URL=https://mole-ia.duckdns.org/api/v1/ bash scripts/verify-staging.sh
#       STAGING_USER=... STAGING_PASS=... bash scripts/verify-staging.sh  (checks con auth)
# Cero secretos en código: credenciales solo por entorno. Exit 1 ante cualquier fallo.
# También sirve contra LAN: BASE_URL=http://<IP-PC>:8000/api/v1/
# =============================================================================
set -euo pipefail

BASE_URL="${BASE_URL:-http://127.0.0.1:8000/api/v1/}"
# Sin slash final: los checks concatenan "/<path>" (doble "//" da 404 en Django).
BASE_URL="${BASE_URL%/}"
FAIL=0

check() { # check <nombre> <condición-comando...>
    local name="$1"; shift
    if "$@" > /dev/null 2>&1; then echo "[OK] $name"; else echo "[FAIL] $name"; FAIL=1; fi
}

echo "== verify-staging contra $BASE_URL =="

# 1. Health público (contrato §5b)
BODY=$(curl -sk -m 10 "$BASE_URL/health/") || BODY=""
echo "$BODY" | grep -q '"status"[[:space:]]*:[[:space:]]*"healthy"' \
    && echo "[OK] health público" || { echo "[FAIL] health público: $BODY"; FAIL=1; }

# 2. Login con credenciales malas → 401 con forma del contrato
CODE=$(curl -sk -m 10 -o /tmp/opencode/staging_login.json -w "%{http_code}" -X POST "$BASE_URL/auth/login/" \
    -H 'Content-Type: application/json' -d '{"username":"nadie","password":"x"}')
[ "$CODE" = "401" ] && grep -q "error" /tmp/opencode/staging_login.json \
    && echo "[OK] login 401 con forma" || { echo "[FAIL] login 401 (code=$CODE)"; FAIL=1; }

# 3. Telemetría sin token → 401 (no filtra datos)
CODE=$(curl -sk -m 10 -o /dev/null -w "%{http_code}" "$BASE_URL/telemetry/latest/?plant_id=00000000-0000-0000-0000-000000000000")
[ "$CODE" = "401" ] && echo "[OK] telemetry exige auth" || { echo "[FAIL] telemetry sin auth (code=$CODE)"; FAIL=1; }

# 4. OpenAPI schema accesible (contrato congelado existe)
SCHEMA_URL="${BASE_URL%/v1}/schema/"
CODE=$(curl -sk -m 15 -o /dev/null -w "%{http_code}" "$SCHEMA_URL")
[ "$CODE" = "200" ] && echo "[OK] /api/schema/ accesible" || { echo "[WARN] /api/schema/ code=$CODE (revisar)"; }

# 5. Login real (solo si STAGING_USER/STAGING_PASS por entorno)
if [ -n "${STAGING_USER:-}" ] && [ -n "${STAGING_PASS:-}" ]; then
    TOKEN=$(curl -sk -m 10 -X POST "$BASE_URL/auth/login/" -H 'Content-Type: application/json' \
        -d "{\"username\":\"$STAGING_USER\",\"password\":\"$STAGING_PASS\"}" | python3 -c "import sys,json; print(json.load(sys.stdin).get('token',''))" 2>/dev/null || true)
    if [ -n "$TOKEN" ]; then
        echo "[OK] login real emite JWT"
        CODE=$(curl -sk -m 10 -o /dev/null -w "%{http_code}" "$BASE_URL/auth/metadata/" -H "Authorization: Bearer $TOKEN")
        [ "$CODE" = "200" ] && echo "[OK] metadata con JWT" || { echo "[FAIL] metadata (code=$CODE)"; FAIL=1; }
    else
        echo "[FAIL] login real no emitió token"; FAIL=1
    fi
else
    echo "[SKIP] login real (sin STAGING_USER/STAGING_PASS)"
fi

[ "$FAIL" = "0" ] && echo "== STAGING-OK ==" || { echo "== STAGING-FAIL =="; exit 1; }
