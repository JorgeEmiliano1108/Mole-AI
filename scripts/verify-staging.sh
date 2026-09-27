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

# 4b. Eventos sin token → 401/403 (issue N-0, sin filtración)
for EP in "user-plants/my-alerts/" "admin/system-events" "admin/audit-log" "admin/devices/"; do
    CODE=$(curl -sk -m 10 -o /dev/null -w "%{http_code}" "$BASE_URL/$EP")
    { [ "$CODE" = "401" ] || [ "$CODE" = "403" ]; } \
        && echo "[OK] $EP exige auth ($CODE)" \
        || { echo "[FAIL] $EP sin auth (code=$CODE, esperado 401/403)"; FAIL=1; }
done

# 5. Login real (solo si STAGING_USER/STAGING_PASS por entorno)
if [ -n "${STAGING_USER:-}" ] && [ -n "${STAGING_PASS:-}" ]; then
    TOKEN=$(curl -sk -m 10 -X POST "$BASE_URL/auth/login/" -H 'Content-Type: application/json' \
        -d "{\"username\":\"$STAGING_USER\",\"password\":\"$STAGING_PASS\"}" | python3 -c "import sys,json; print(json.load(sys.stdin).get('token',''))" 2>/dev/null || true)
    if [ -n "$TOKEN" ]; then
        echo "[OK] login real emite JWT"
        CODE=$(curl -sk -m 10 -o /dev/null -w "%{http_code}" "$BASE_URL/auth/metadata/" -H "Authorization: Bearer $TOKEN")
        [ "$CODE" = "200" ] && echo "[OK] metadata con JWT" || { echo "[FAIL] metadata (code=$CODE)"; FAIL=1; }
        # 5b. RBAC eventos (issue N-0): my-alerts 200 con forma, system-events
        # 403 para botánico (solo admin). STAGING_ADMIN_* habilita el caso admin.
        BODY=$(curl -sk -m 10 "$BASE_URL/user-plants/my-alerts/" -H "Authorization: Bearer $TOKEN") || BODY=""
        echo "$BODY" | grep -q '"alerts"' \
            && echo "[OK] my-alerts 200 con forma" || { echo "[FAIL] my-alerts: $BODY"; FAIL=1; }
        CODE=$(curl -sk -m 10 -o /dev/null -w "%{http_code}" "$BASE_URL/admin/system-events" -H "Authorization: Bearer $TOKEN")
        [ "$CODE" = "403" ] && echo "[OK] system-events 403 para botánico" || { echo "[WARN] system-events botánico code=$CODE (esperado 403 si no es staff)"; }
        if [ -n "${STAGING_ADMIN_USER:-}" ] && [ -n "${STAGING_ADMIN_PASS:-}" ]; then
            ATOKEN=$(curl -sk -m 10 -X POST "$BASE_URL/auth/login/" -H 'Content-Type: application/json' \
                -d "{\"username\":\"$STAGING_ADMIN_USER\",\"password\":\"$STAGING_ADMIN_PASS\"}" | python3 -c "import sys,json; print(json.load(sys.stdin).get('token',''))" 2>/dev/null || true)
            if [ -n "$ATOKEN" ]; then
                BODY=$(curl -sk -m 40 "$BASE_URL/admin/system-events" -H "Authorization: Bearer $ATOKEN") || BODY=""
                for SEC in security devices telemetry services; do
                    echo "$BODY" | grep -q "\"$SEC\"" \
                        && echo "[OK] system-events sección $SEC" \
                        || { echo "[FAIL] system-events sin sección $SEC"; FAIL=1; }
                done
            else
                echo "[FAIL] login admin no emitió token"; FAIL=1
            fi
        else
            echo "[SKIP] system-events admin (sin STAGING_ADMIN_USER/STAGING_ADMIN_PASS)"
        fi
    else
        echo "[FAIL] login real no emitió token"; FAIL=1
    fi
else
    echo "[SKIP] login real (sin STAGING_USER/STAGING_PASS)"
fi

[ "$FAIL" = "0" ] && echo "== STAGING-OK ==" || { echo "== STAGING-FAIL =="; exit 1; }
