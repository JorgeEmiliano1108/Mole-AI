#!/usr/bin/env bash
# =============================================================================
# check-docs-consistency.sh — Verifica endpoints documentados vs código real
#
# TDD: este script debe fallar (RED) cuando la documentación está desactualizada
#      y pasar (GREEN) cuando la documentación refleja fielmente el código.
# =============================================================================
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
DOCS="$ROOT/frontend/docs/requisitos.md"
CORE="$ROOT/core_backend"

ERRORS=0
WARNINGS=0

echo "═══════════════════════════════════════════════════════════════"
echo "  check-docs-consistency.sh — Endpoints vs urls.py "
echo "═══════════════════════════════════════════════════════════════"
echo ""

# ── Helper: build real-route list from urls.py ──────────────────────────
# Usage: extract_routes <app_dir> <url_prefix>
extract_routes() {
    local app_dir="$1"
    local prefix="$2"
    local urls_file="$app_dir/urls.py"
    if [ ! -f "$urls_file" ]; then
        # Try urls_user.py or similar variants
        for variant in "$app_dir"/urls*.py; do
            [ -f "$variant" ] && extract_routes_from_file "$variant" "$prefix"
        done
        return
    fi
    extract_routes_from_file "$urls_file" "$prefix"
}

extract_routes_from_file() {
    local file="$1"
    local prefix="$2"
    # Collapse multi-line path() calls into single lines, extract first quoted arg
    python3 -c "
import re, sys
with open('$file') as f:
    content = f.read()
# Remove comments
content = re.sub(r'#.*$', '', content, flags=re.MULTILINE)
# Normalize whitespace
content = re.sub(r'\s+', ' ', content)
# Find all path('...') or path(\"...\") calls (including empty-string routes)
for m in re.finditer(r\"\"\"path\(\\s*['\\\"]([^'\\\"]*)['\\\"]\"\"\", content):
    route = m.group(1)
    # Empty string means mounted at prefix root (e.g. plants/ → /api/v1/plants/)
    print('$prefix' + route)
" 2>/dev/null || true
}

BUILD_REAL=$(mktemp)
trap 'rm -f "$BUILD_REAL"' EXIT

# Root-level routes (not under api/v1/)
echo "/health/" >> "$BUILD_REAL"

# Auth: api/v1/auth/
extract_routes "$CORE/apps/authentication" "/api/v1/auth/" >> "$BUILD_REAL"

# AI Models: api/v1/ai/
extract_routes "$CORE/apps/ai_models" "/api/v1/ai/" >> "$BUILD_REAL"

# Training Data: api/v1/training/
extract_routes "$CORE/apps/training_data" "/api/v1/training/" >> "$BUILD_REAL"

# Core (catch-all under api/v1/): api/v1/
extract_routes "$CORE/apps/core" "/api/v1/" >> "$BUILD_REAL"

# Plants: api/v1/plants/
extract_routes "$CORE/apps/plants" "/api/v1/plants/" >> "$BUILD_REAL"

# User Plants: api/v1/user-plants/
extract_routes_from_file "$CORE/apps/plants/urls_user.py" "/api/v1/user-plants/" >> "$BUILD_REAL"

# DRF Router routes: species ViewSet generates CRUD at plants/species/
echo "/api/v1/plants/species/" >> "$BUILD_REAL"

# Clean blank lines, sort, dedup
sort -u "$BUILD_REAL" -o "$BUILD_REAL"

echo "Rutas reales encontradas en core_backend/apps/*/urls.py:"
wc -l < "$BUILD_REAL" | tr -d ' '
echo ""

# ── Extract documented endpoints from requisitos.md §7 ──────────────────
DOC_ENDPOINTS=$(mktemp)
trap 'rm -f "$DOC_ENDPOINTS" "$BUILD_REAL"' EXIT

python3 -c "
import re
with open('$DOCS') as f:
    content = f.read()

# Find section 7
m = re.search(r'## 7\. Endpoints.*?(?=^## [0-9])', content, re.MULTILINE | re.DOTALL)
if m:
    section = m.group(0)
    for line in section.split('\n'):
        line = line.strip()
        if line.startswith('|') and line.count('|') >= 4:
            if 'Método' in line or '---' in line or not line:
                continue
            cols = [c.strip().strip('\`') for c in line.split('|')]
            # Filter out empty leading/trailing from split
            cols = [c for c in cols if c != '']
            # Table variants:
            # 4 cols: §7.1 → Método | Path | Auth | Propósito  (implicit core_backend)
            # 5 cols: §7.2 → Método | Path | Microservicio | Auth | Propósito
            if len(cols) >= 4:
                path = cols[1] if len(cols) > 1 else ''
                if len(cols) >= 5:
                    micro = cols[2]  # §7.2 format
                else:
                    micro = 'core_backend'  # §7.1 format, implicit
                if path:
                    print(f'{micro}\t{path}')
" >> "$DOC_ENDPOINTS"

echo "Endpoints documentados en requisitos.md §7 (con microservicio):"
wc -l < "$DOC_ENDPOINTS" | tr -d ' '
echo ""

# ── Compare ─────────────────────────────────────────────────────────────
echo "─── Análisis de endpoints documentados como 'core_backend' ───"
echo ""

# Split into core_backend vs microservice endpoints
CORE_DOCS=$(grep $'^core_backend\t' "$DOC_ENDPOINTS" || true)
MICRO_DOCS=$(grep -v $'^core_backend\t' "$DOC_ENDPOINTS" || true)

while IFS=$'\t' read -r micro path; do
    [ -z "$path" ] && continue

    # Normalize path: strip backticks, whitespace, normalize params (both {} and <> styles)
    path_clean=$(echo "$path" | sed 's/`//g; s/{[^}]*}//g; s/<[^>]*>//g; s/ *$//; s/^ *//')

    # Check if this path exists in real routes
    # Normalize real routes similarly for matching
    found=0
    while IFS= read -r real; do
        # Strip all parameter markers to compare path structure
        real_base=$(echo "$real" | sed 's/<[^>]*>//g; s|/$||')
        path_base=$(echo "$path_clean" | sed 's|/$||')
        if [ "$real_base" = "$path_base" ]; then
            found=1
            break
        fi
    done < "$BUILD_REAL"

    if [ "$found" -eq 0 ]; then
        echo "  ❌ SOBRAN_EN_DOCS: $path_clean — NO EXISTE en urls.py"
        ERRORS=$((ERRORS + 1))
    else
        echo "  ✅ OK: $path_clean"
    fi
done <<< "$CORE_DOCS"

echo ""
echo "─── Endpoints de microservicios (mole_chat, mole_vision, mole_report) ───"
echo "  (No verificados contra core_backend — son ruteados por Nginx a microservicios)"
echo ""

while IFS=$'\t' read -r micro path; do
    [ -z "$path" ] && continue
    path_clean=$(echo "$path" | sed 's/`//g; s/ *$//; s/^ *//')
    echo "  ⚠️  No verificado: $path_clean → $micro"
    WARNINGS=$((WARNINGS + 1))
done <<< "$MICRO_DOCS"

echo ""
echo "─── Rutas reales NO documentadas en requisitos.md ───"
echo ""

# Check which real routes are missing from docs
while IFS= read -r real; do
    found=0
    while IFS=$'\t' read -r micro path; do
        [ -z "$path" ] && continue
        path_clean=$(echo "$path" | sed 's/`//g; s/{[^}]*}//g; s/<[^>]*>//g; s/ *$//; s/^ *//; s|/$||')
        real_base=$(echo "$real" | sed 's/<[^>]*>//g; s|/$||')
        if [ "$real_base" = "$path_clean" ]; then
            found=1
            break
        fi
    done < "$DOC_ENDPOINTS"

    if [ "$found" -eq 0 ]; then
        echo "  ➕ FALTAN_EN_DOCS: $real"
    fi
done < "$BUILD_REAL"

echo ""
echo "═══════════════════════════════════════════════════════════════"
if [ "$ERRORS" -gt 0 ]; then
    echo "  RESULTADO: ❌ RED — $ERRORS endpoint(s) documentados no existen"
    exit 1
else
    echo "  RESULTADO: ✅ GREEN — Todos los endpoints documentados existen"
fi
echo "  Warnings (microservicios no verificados): $WARNINGS"
echo "═══════════════════════════════════════════════════════════════"
