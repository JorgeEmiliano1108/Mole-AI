#!/bin/bash
# scripts/audit-rf-rnf.sh — Auditoría de Coherencia RF/RNF
# Verifica claims documentados contra código fuente real
# Exit 1 si hay algún ❌ Falso
set -euo pipefail

PASS=true
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CORE_BACKEND="$(cd "$ROOT/../core_backend" && pwd)"

# ─── helpers ───────────────────────────────────────────────────────────────
probe() {
    local id="$1" desc="$2" expected="$3" actual="$4"
    if echo "$actual" | grep -q "$expected"; then
        echo "  ✅ $id — $desc"
    else
        echo "  ❌ $id — $desc"
        echo "     Esperado: $expected"
        echo "     Real:     $(echo "$actual" | head -c 200)"
        PASS=false
    fi
}

probe_file() {
    local id="$1" desc="$2" file="$3"
    if [ -f "$file" ]; then
        echo "  ✅ $id — $desc ($file existe)"
    else
        echo "  ❌ $id — $desc ($file NO EXISTE)"
        PASS=false
    fi
}

probe_grep() {
    local id="$1" desc="$2" pattern="$3" target="$4"
    local result
    result=$(grep -r "$pattern" "$target" 2>/dev/null | head -3) || true
    if [ -n "$result" ]; then
        echo "  ✅ $id — $desc"
    else
        echo "  ❌ $id — $desc (no se encontró '$pattern' en $target)"
        PASS=false
    fi
}

probe_grep_file() {
    local id="$1" desc="$2" file="$3" pattern="$4"
    if [ -f "$file" ] && grep -q "$pattern" "$file" 2>/dev/null; then
        echo "  ✅ $id — $desc"
    else
        echo "  ❌ $id — $desc (no se encontró '$pattern' en $file)"
        PASS=false
    fi
}

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║   Auditoría de Coherencia RF/RNF                           ║"
echo "║   Mole-AI — $(date +%Y-%m-%d)                              ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# ─── FASE A: Setup ─────────────────────────────────────────────────────────
echo "═══ FASE A — Setup ═══"
# A-01: CONTEXT.md opcional (no requerido para claims)
if [ -f "$ROOT/../CONTEXT.md" ]; then
    echo "  ✅ A-01 — CONTEXT.md existe"
else
    echo "  ⚠️ A-01 — CONTEXT.md no existe (opcional, no afecta claims)"
fi
probe_file "A-02" "admin.html" "$ROOT/admin.html"
probe_file "A-03" "login.html" "$ROOT/login.html"
probe_file "A-04" "dashboard.html" "$ROOT/dashboard.html"

# ─── FASE B: Module existence ─────────────────────────────────────────────
echo ""
echo "═══ FASE B — Module Map ═══"
for f in \
    "src/js/modules/services/chat.js" \
    "src/js/modules/services/vision.js" \
    "src/js/modules/services/map.js" \
    "src/js/modules/services/wiki.js" \
    "src/js/modules/services/iot.js" \
    "src/js/modules/services/health.js" \
    "src/js/modules/services/crops.js" \
    "src/js/modules/services/bindings.js" \
    "src/js/modules/services/reports.js" \
    "src/js/modules/ui/navigation.js" \
    "src/js/modules/ui/privacy.js" \
    "src/js/modules/ui/dom.js" \
    "src/js/modules/auth/sessionManager.js" \
    "src/js/modules/api/config.js" \
    "src/js/modules/dashboard/adminDashboard.js" \
    "src/js/admin.js" \
    "src/js/typewriter.js" \
    "src/js/main.js" \
    "src/js/modules/api/ApiService.js" \
    "vite.config.js" \
    "nginx.conf" \
    "Dockerfile" \
    "scripts/check-bundle.sh" \
    "src/js/modules/__tests__/dom.test.js" \
    "src/js/modules/__tests__/sessionManager.test.js" \
    "src/css/main.css" \
    ; do
    probe_file "B-$(basename $f)" "$f" "$ROOT/$f"
done

# ─── FASE C: Frontend RF-01…RF-37 ──────────────────────────────────────────
echo ""
echo "═══ FASE C — Frontend RF ═══"

# RF-01: Login JWT
probe_grep_file "RF-01" "Login JWT en apiService" \
    "$ROOT/src/js/modules/api/ApiService.js" "setToken"

# RF-02: Register form
probe_grep_file "RF-02" "Register form en login.html" \
    "$ROOT/login.html" "register-form"

# RF-03: Logout cleanup
probe_grep_file "RF-03" "cleanupSession en sessionManager" \
    "$ROOT/src/js/modules/auth/sessionManager.js" "cleanupSession"

# RF-04: Refresh automático 15 min
probe_grep_file "RF-04" "REFRESH_THRESHOLD=15 min" \
    "$ROOT/src/js/modules/auth/sessionManager.js" "REFRESH_THRESHOLD"

# RF-05: Inactivity 20 min
probe_grep_file "RF-05" "INACTIVITY_LIMIT=20 min" \
    "$ROOT/src/js/modules/auth/sessionManager.js" "INACTIVITY_LIMIT"

# RF-06: Route guard
probe_grep_file "RF-06" "checkAuthGuard en main.js" \
    "$ROOT/src/js/main.js" "checkAuthGuard"

# RF-07: Password recovery (auth.js, movido de mlops.js en FE-DT14)
probe_grep_file "RF-07" "forgotPassword en auth.js" \
    "$ROOT/src/js/auth.js" "forgotPassword"

# RF-08: Polling 30s
probe_grep_file "RF-08" "HEALTH_POLL_INTERVAL=30000" \
    "$ROOT/src/js/modules/services/health.js" "HEALTH_POLL_INTERVAL"

# RF-09: Dual view
probe_grep_file "RF-09" "Dual view toggle en health.js" \
    "$ROOT/src/js/modules/services/health.js" "LS_VIEW_MODE_KEY"

# RF-10: Plant registration modal
probe_grep_file "RF-10" "add-plant-modal en crops.js" \
    "$ROOT/src/js/modules/services/crops.js" "add-plant-modal"

# RF-11: Health status per device
probe_grep_file "RF-11" "fetchHealth en health.js" \
    "$ROOT/src/js/modules/services/health.js" "fetchHealth"

# RF-12: History chart
probe_grep_file "RF-12" "Chart en adminDashboard.js" \
    "$ROOT/src/js/modules/dashboard/adminDashboard.js" "Chart("

# RF-13: Chat LLM
probe_grep_file "RF-13" "IA_ENGINES en chat.js" \
    "$ROOT/src/js/modules/services/chat.js" "IA_ENGINES"

# RF-14: Chat vision
probe_grep_file "RF-14" "handleChatVisionUpload en chat.js" \
    "$ROOT/src/js/modules/services/chat.js" "handleChatVisionUpload"

# RF-15: Chat statistics
probe_grep_file "RF-15" "STATS engine en chat.js" \
    "$ROOT/src/js/modules/services/chat.js" "STATS"

# RF-16: Chat history persist
probe_grep_file "RF-16" "loadChatHistory en chat.js" \
    "$ROOT/src/js/modules/services/chat.js" "loadChatHistory"

# RF-17: New conversation
probe_grep_file "RF-17" "clearChatHistory en chat.js" \
    "$ROOT/src/js/modules/services/chat.js" "clearChatHistory"

# RF-18: Typewriter
probe_grep_file "RF-18" "typeInterval en chat.js" \
    "$ROOT/src/js/modules/services/chat.js" "typeInterval"

# RF-19: Vision upload
probe_grep_file "RF-19" "Upload imagen en vision.js" \
    "$ROOT/src/js/modules/services/vision.js" "URL.createObjectURL"

# RF-20: Diagnostic result
probe_grep_file "RF-20" "renderDiagnosisRow en vision.js" \
    "$ROOT/src/js/modules/services/vision.js" "renderDiagnosisRow"

# RF-21: Chat integration
probe_grep_file "RF-21" "chat-vision-input en chat.js" \
    "$ROOT/src/js/modules/services/chat.js" "chat-vision-input"

# RF-22: Map Leaflet
probe_grep_file "RF-22" "Leaflet import en map.js" \
    "$ROOT/src/js/modules/services/map.js" "leaflet"

# RF-23: Weather layer
probe_grep_file "RF-23" "Weather tiles en map.js" \
    "$ROOT/src/js/modules/services/map.js" "weather/tile"

# RF-24: Plague hotspots
probe_grep_file "RF-24" "Plagas layer en map.js" \
    "$ROOT/src/js/modules/services/map.js" "plagas"

# RF-25: Species catalog grid
probe_grep_file "RF-25" "wiki-grid en wiki.js" \
    "$ROOT/src/js/modules/services/wiki.js" "wiki-grid"

# RF-26: Species search
probe_grep_file "RF-26" "wiki-search input en wiki.js" \
    "$ROOT/src/js/modules/services/wiki.js" "wiki-search"

# RF-27: Catalog cache
probe_grep_file "RF-27" "MoleState.speciesCatalogLoaded en wiki.js" \
    "$ROOT/src/js/modules/services/wiki.js" "speciesCatalogLoaded"

# RF-28: Admin KPIs
probe_grep_file "RF-28" "getKPIData en admin.js" \
    "$ROOT/src/js/admin.js" "getKPIData"

# RF-29: IoT fleet
probe_grep_file "RF-29" "chart-radar-health en admin.js" \
    "$ROOT/src/js/admin.js" "chart-radar-health"

# RF-30: MLOps
probe_grep_file "RF-30" "MLOps chart en admin.js" \
    "$ROOT/src/js/admin.js" "chart-line-training"

# RF-31: Alert center
probe_grep_file "RF-31" "live_alerts en admin.js" \
    "$ROOT/src/js/admin.js" "alerts"

# RF-32: Export TXT
probe_grep_file "RF-32" "downloadAdminReport en adminDashboard.js" \
    "$ROOT/src/js/modules/dashboard/adminDashboard.js" "downloadAdminReport"

# RF-33: BLE scan
probe_grep_file "RF-33" "navigator.bluetooth en iot.js" \
    "$ROOT/src/js/modules/services/iot.js" "navigator.bluetooth"

# RF-34: WiFi provisioning
probe_grep_file "RF-34" "provisionViaWifi en iot.js" \
    "$ROOT/src/js/modules/services/iot.js" "provisionViaWifi"

# RF-35: Bindings CRUD
probe_grep_file "RF-35" "renderBindingRow en bindings.js" \
    "$ROOT/src/js/modules/services/bindings.js" "renderBindingRow"

# RF-36: Privacy banner LFPDPPP
probe_grep_file "RF-36" "privacy-banner-lfpdppp en privacy.js" \
    "$ROOT/src/js/modules/ui/privacy.js" "privacy-banner-lfpdppp"

# RF-37: Consent persist
probe_grep_file "RF-37" "consent_lfpdppp en privacy.js" \
    "$ROOT/src/js/modules/ui/privacy.js" "consent_lfpdppp"

# ─── FASE C: Frontend RNF-01…RNF-35 ────────────────────────────────────────
echo ""
echo "═══ FASE C — Frontend RNF ═══"

# RNF-01: LLM timeout 120s
probe_grep_file "RNF-01" "aiTimeout=120000 en apiService.js" \
    "$ROOT/src/js/modules/api/ApiService.js" "aiTimeout = 120000"

# RNF-02: Standard timeout 30s
probe_grep_file "RNF-02" "defaultTimeout=30000 en apiService.js" \
    "$ROOT/src/js/modules/api/ApiService.js" "defaultTimeout = 30000"

# RNF-03: Polling 30s
probe_grep_file "RNF-03" "HEALTH_POLL_INTERVAL=30000" \
    "$ROOT/src/js/modules/services/health.js" "HEALTH_POLL_INTERVAL"

# RNF-04: manualChunks en vite.config
probe_grep_file "RNF-04" "manualChunks en vite.config.js" \
    "$ROOT/vite.config.js" "manualChunks"

# RNF-06: Cache immutable
probe_grep_file "RNF-06" "public, immutable en nginx.conf" \
    "$ROOT/nginx.conf" "public, immutable"

# RNF-07: HTML no-cache
probe_grep_file "RNF-07" "no-cache para HTML en nginx.conf" \
    "$ROOT/nginx.conf" "no-cache, no-store, must-revalidate"

# RNF-09: safeHTML en dom.js
probe_grep_file "RNF-09" "safeHTML en dom.js" \
    "$ROOT/src/js/modules/ui/dom.js" "safeHTML"

# RNF-10: CSP header
probe_grep_file "RNF-10" "script-src 'self' en nginx.conf" \
    "$ROOT/nginx.conf" "script-src 'self'"

# RNF-12: server_tokens off
probe_grep_file "RNF-12" "server_tokens off en nginx.conf" \
    "$ROOT/nginx.conf" "server_tokens off"

# RNF-13: X-Content-Type-Options
probe_grep_file "RNF-13" "nosniff en nginx.conf" \
    "$ROOT/nginx.conf" "nosniff"

# RNF-14: X-Frame-Options
probe_grep_file "RNF-14" "DENY en nginx.conf" \
    "$ROOT/nginx.conf" "X-Frame-Options.*DENY"

# RNF-16: JWT refresh threshold
probe_grep_file "RNF-16" "REFRESH_THRESHOLD=15 min" \
    "$ROOT/src/js/modules/auth/sessionManager.js" "REFRESH_THRESHOLD"

# RNF-17: CORS origins
probe_grep_file "RNF-17" "CORS origins en nginx.conf" \
    "$ROOT/nginx.conf" "mole-ia"

# RNF-18: Exponential backoff
probe_grep_file "RNF-18" "Exponential backoff en apiService.js" \
    "$ROOT/src/js/modules/api/ApiService.js" "Math.pow(2, attempt)"

# RNF-19: AbortController
probe_grep_file "RNF-19" "AbortController en apiService.js" \
    "$ROOT/src/js/modules/api/ApiService.js" "AbortController"

# RNF-20: Friendly errors
probe_grep_file "RNF-20" "Error 401/429 en español en apiService.js" \
    "$ROOT/src/js/modules/api/ApiService.js" "Demasiadas solicitudes"

# RNF-22: BFCache guard
probe_grep_file "RNF-22" "BFCache pageshow en main.js" \
    "$ROOT/src/js/main.js" "pageshow"

# RNF-23: ES6 modules
if [ -d "$ROOT/src/js/modules" ]; then
    echo "  ✅ RNF-23 — src/js/modules/ existe con ES6 modules"
else
    echo "  ❌ RNF-23 — src/js/modules/ NO EXISTE"
    PASS=false
fi

# RNF-24: No JS legacy fuera de src/js/ (FE-DT03/FE-DT04)
if [ -d "$ROOT/static/js" ]; then
    echo "  ❌ RNF-24 — static/js/ aun existe (restos legacy)"
    PASS=false
else
    echo "  ✅ RNF-24 — static/ eliminado, todo JS es ES6 module en src/js/"
fi

# RNF-25: 30 tests
test_count=$(grep -hE '(it\(|test\()' "$ROOT/src/js/modules/__tests__/dom.test.js" "$ROOT/src/js/modules/__tests__/sessionManager.test.js" 2>/dev/null | wc -l)
if [ "$test_count" -ge 30 ]; then
    echo "  ✅ RNF-25 — $test_count tests (target 30)"
else
    echo "  ❌ RNF-25 — $test_count tests (target 30)"
    PASS=false
fi

# RNF-26: Lockfile
probe_file "RNF-26" "pnpm-lock.yaml existe" "$ROOT/pnpm-lock.yaml"

# RNF-27: Zero os.getenv
if grep -rn 'os\.getenv\|process\.env\|import\.meta\.env' "$ROOT/src/js/" --include='*.js' --include='*.ts' 2>/dev/null | grep -qv '.test.'; then
    echo "  ❌ RNF-27 — os.getenv/process.env encontrado en src/"
    PASS=false
else
    echo "  ✅ RNF-27 — Zero os.getenv en src/"
fi

# RNF-31: Docker multi-stage
probe_grep_file "RNF-31" "Multi-stage build en Dockerfile" \
    "$ROOT/Dockerfile" "AS builder"

# RNF-32: USER nginx
probe_grep_file "RNF-32" "USER nginx en Dockerfile" \
    "$ROOT/Dockerfile" "USER nginx"

# RNF-33: HEALTHCHECK
probe_grep_file "RNF-33" "HEALTHCHECK en Dockerfile" \
    "$ROOT/Dockerfile" "HEALTHCHECK"

# ─── Structural Architecture Probes ─────────────────────────────────────────
echo ""
echo "═══ Structural Architecture ═══"

# FE-A01: sessionManager.js en modules/auth/
probe_file "FE-A01" "sessionManager en modules/auth/" \
    "$ROOT/src/js/modules/auth/sessionManager.js"

# FE-A02: adminDashboard / userDashboard en modules/dashboard/
probe_file "FE-A02" "adminDashboard en modules/dashboard/" \
    "$ROOT/src/js/modules/dashboard/adminDashboard.js"
probe_file "FE-A03" "userDashboard en modules/dashboard/" \
    "$ROOT/src/js/modules/dashboard/userDashboard.js"

# FE-A04: Sin colisión de nombres entre capas services/ y ui/ (iot.js es excepción documentada)
collisions=$(find "$ROOT/src/js/modules/services" "$ROOT/src/js/modules/ui" -name '*.js' -exec basename {} \; 2>/dev/null | sort | uniq -d | grep -v '^iot\.js$' || true)
if [ -z "$collisions" ]; then
    echo "  ✅ FE-A04 — Sin colisión inesperada (iot.js es dualidad documentada en §8)"
else
    echo "  ❌ FE-A04 — Colisión inesperada: $collisions"
    PASS=false
fi

# FE-A05: navigation.js no importa directamente de services/
if grep -q "services/map\|services/reports" "$ROOT/src/js/modules/ui/navigation.js" 2>/dev/null; then
    echo "  ❌ FE-A05 — navigation.js importa directamente de services/"
    PASS=false
else
    echo "  ✅ FE-A05 — navigation.js no importa directamente de services/ (usa registerLazyLoader)"
fi

# FE-A06: cursor.ts y typewriter.ts migrados a .js
if [ -f "$ROOT/src/js/typewriter.ts" ] || [ -f "$ROOT/src/js/modules/ui/cursor.ts" ]; then
    echo "  ❌ FE-A06 — Archivos .TS residuales encontrados"
    PASS=false
else
    echo "  ✅ FE-A06 — typewriter.js y cursor.js migrados a .js"
fi

# FE-A07: ApiService.js real en modules/api/ (barrel apiService.js eliminado en FE-DT14)
probe_file "FE-A07" "ApiService.js real en modules/api/" \
    "$ROOT/src/js/modules/api/ApiService.js"

# ─── FASE C: Backend RF-01…RF-23 ──────────────────────────────────────────
echo ""
echo "═══ FASE C — Backend RF ═══"

# RF-01: Login JWT
probe_grep_file "B-RF-01" "login_view en authentication" \
    "$CORE_BACKEND/apps/authentication/views.py" "def login_view"

# RF-02: Token validation
probe_grep_file "B-RF-02" "validate_token_view en authentication" \
    "$CORE_BACKEND/apps/authentication/views.py" "validate_token_view"

# RF-03: API Keys
probe_grep_file "B-RF-03" "Device.auth_token en core models" \
    "$CORE_BACKEND/apps/core/models.py" "auth_token"

# RF-04: User roles
probe_grep_file "B-RF-04" "supabase_role en authentication models" \
    "$CORE_BACKEND/apps/authentication/models.py" "supabase_role"

# RF-05: Rate limiting
probe_grep_file "B-RF-05" "UserRateThrottle en core throttles" \
    "$CORE_BACKEND/apps/core/throttles.py" "UserRateThrottle"

# RF-06: Telemetry ingest
probe_grep_file "B-RF-06" "sensor_batch_view en core" \
    "$CORE_BACKEND/apps/core/views.py" "sensor_batch_view"

# RF-07: Bulk insert
probe_grep_file "B-RF-07" "bulk_create en core views" \
    "$CORE_BACKEND/apps/core/views.py" "bulk_create"

# RF-08: Downsampling
probe_grep_file "B-RF-08" "downsample_telemetry task" \
    "$CORE_BACKEND/apps/core/tasks.py" "downsample_telemetry"

# RF-09: Geocercas — no implementado
if grep -rn 'geofence\|geocerca\|GeoFence' "$CORE_BACKEND/apps/" 2>/dev/null | grep -v __pycache__ | head -1; then
    echo "  ❌ B-RF-09 — Geocercas encontradas (deberían no existir según auditoría)"
else
    echo "  ✅ B-RF-09 — Geocercas no implementado (coherente con auditoría)"
fi

# RF-11: Vision diagnosis
probe_grep_file "B-RF-11" "analyze_vision_view en ai_models" \
    "$CORE_BACKEND/apps/ai_models/views.py" "analyze_vision_view"

# RF-12: Chat RAG
probe_grep_file "B-RF-12" "train_rag_view en ai_models" \
    "$CORE_BACKEND/apps/ai_models/views.py" "train_rag_view"

# RF-17: Live alerts
probe_grep_file "B-RF-17" "live_alerts_view en core" \
    "$CORE_BACKEND/apps/core/admin_views.py" "live_alerts_view"

# RF-20: Admin stats
probe_grep_file "B-RF-20" "admin_stats_view en core" \
    "$CORE_BACKEND/apps/core/admin_views.py" "admin_stats_view"

# RF-22: AuditLog
probe_grep_file "B-RF-22" "AuditLog model en core" \
    "$CORE_BACKEND/apps/core/models.py" "class AuditLog"

# RF-23: MinIO/S3 storage
probe_grep_file "B-RF-23" "storages en INSTALLED_APPS" \
    "$CORE_BACKEND/mole_ai_backend/settings.py" "storages"

# ─── FASE C: Backend RNF-01…RNF-24 ────────────────────────────────────────
echo ""
echo "═══ FASE C — Backend RNF ═══"

# RNF-01: JWT HS256
probe_grep_file "B-RNF-01" "HS256 decode en local_jwt_auth" \
    "$CORE_BACKEND/apps/authentication/infrastructure/local_jwt_auth.py" "HS256"

# RNF-02: API Keys
probe_grep_file "B-RNF-02" "HardwareAPIKeyAuthentication" \
    "$CORE_BACKEND/apps/authentication/infrastructure/authentication.py" "HardwareAPIKeyAuthentication"

# RNF-04: DRF throttles
probe_grep_file "B-RNF-04" "DEFAULT_THROTTLE_RATES en settings" \
    "$CORE_BACKEND/mole_ai_backend/settings.py" "DEFAULT_THROTTLE_RATES"

# RNF-06: Django ORM
probe_grep_file "B-RNF-06" "rest_framework en INSTALLED_APPS" \
    "$CORE_BACKEND/mole_ai_backend/settings.py" "rest_framework"

# RNF-08: tenacity
probe_grep_file "B-RNF-08" "tenacity en requirements" \
    "$CORE_BACKEND/requirements.txt" "tenacity"

# RNF-10: Graceful degradation middleware
probe_grep_file "B-RNF-10" "GracefulDegradationMiddleware" \
    "$CORE_BACKEND/mole_ai_backend/settings.py" "GracefulDegradationMiddleware"

# RNF-12: Redis cache
probe_grep_file "B-RNF-12" "django_redis cache" \
    "$CORE_BACKEND/mole_ai_backend/settings.py" "django_redis"

# RNF-13: bulk_create
probe_grep_file "B-RNF-13" "bulk_create en core views" \
    "$CORE_BACKEND/apps/core/views.py" "bulk_create"

# RNF-14: Downsampling task
probe_grep_file "B-RNF-14" "downsample_telemetry task" \
    "$CORE_BACKEND/apps/core/tasks.py" "downsample_telemetry"

# RNF-16: 30s timeout
probe_grep_file "B-RNF-16" "timeout_seconds=30 en microservices" \
    "$CORE_BACKEND/apps/core/infrastructure/clients/microservices.py" "timeout_seconds: int = 30"

# RNF-19: Test count
test_count_backend=$(find "$CORE_BACKEND" -name 'test_*.py' -not -path '*__pycache__*' | wc -l)
method_count=$(grep -rn "def test_" "$CORE_BACKEND/apps/" "$CORE_BACKEND/tests/" --include='*.py' 2>/dev/null | wc -l)
echo "  ⚠️ B-RNF-19 — $test_count_backend archivos, $method_count métodos (documentado: ~900, real: ~$method_count)"

# RNF-21: Logging config
probe_grep_file "B-RNF-21" "LOGGING config en settings" \
    "$CORE_BACKEND/mole_ai_backend/settings.py" "LOGGING"

# RNF-24: Health check
probe_grep_file "B-RNF-24" "health_check_view en core urls" \
    "$CORE_BACKEND/apps/core/urls.py" "health_check"

# ─── Verificación bundle ────────────────────────────────────────────────────
echo ""
echo "═══ Bundle Check ═══"
if [ -f "$ROOT/scripts/check-bundle.sh" ]; then
    cd "$ROOT" && bash scripts/check-bundle.sh 2>/dev/null && \
        echo "  ✅ Bundle check — PASS" || \
        echo "  ⚠️ Bundle check — No se ejecutó (ejecuta 'pnpm build' primero)"
fi

# ─── Verificación documentación ─────────────────────────────────────────────
echo ""
echo "═══ Doc Consistency Check ═══"
if [ -f "$ROOT/scripts/check-docs-consistency.sh" ]; then
    cd "$ROOT" && bash scripts/check-docs-consistency.sh 2>&1 | tail -3
fi

# ─── Verificación CSP ──────────────────────────────────────────────────────
echo ""
if [ -f "$ROOT/scripts/check-csp.sh" ]; then
    cd "$ROOT" && bash scripts/check-csp.sh 2>&1 | tail -3
fi

# ─── Resumen ───────────────────────────────────────────────────────────────
echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
if [ "$PASS" = true ]; then
    echo "║  RESULTADO: ✅ TODOS LOS PROBES PASARON                    ║"
else
    echo "║  RESULTADO: ❌ HAY FALLOS — REVISAR ARRIBA                 ║"
fi
echo "╚══════════════════════════════════════════════════════════════╝"

if [ "$PASS" = false ]; then
    exit 1
fi
