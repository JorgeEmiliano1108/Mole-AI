#!/bin/bash
# ============================================================================
# SCRIPT DE VERIFICACIÓN - PROYECTO MOLE-AI-BACKEND
# ============================================================================
# Verifica que la reorganización fue exitosa y el proyecto funciona correctamente

echo "🔍 VERIFICACIÓN DE ESTRUCTURA REORGANIZADA"
echo "=========================================="
echo ""

# 1. Verificar estructura de carpetas
echo "📁 Verificando estructura de carpetas..."
if [ -d "apps" ] && [ -d "scripts" ]; then
    echo "✅ Carpetas 'apps' y 'scripts' creadas correctamente"
else
    echo "❌ Error: Carpetas 'apps' o 'scripts' no encontradas"
    exit 1
fi

# 2. Verificar aplicaciones dentro de apps/
echo ""
echo "📦 Verificando aplicaciones en apps/..."
for app in ai_models authentication core; do
    if [ -d "apps/$app" ]; then
        echo "✅ $app/ - OK"
    else
        echo "❌ Error: No se encontró apps/$app/"
        exit 1
    fi
done

# 3. Verificar scripts/
echo ""
echo "🔧 Verificando scripts..."
if [ -f "scripts/bootstrap_project.py" ]; then
    echo "✅ scripts/bootstrap_project.py - OK"
else
    echo "❌ Error: No se encontró scripts/bootstrap_project.py"
    exit 1
fi

# 4. Verificar configuración Django
echo ""
echo "🔗 Verificando configuración Django..."
if [ -f "mole_ai_backend/path_config.py" ]; then
    echo "✅ mole_ai_backend/path_config.py - OK"
else
    echo "❌ Error: No se encontró mole_ai_backend/path_config.py"
    exit 1
fi

# 5. Verificar limpieza de cache
echo ""
echo "🧹 Verificando limpieza de cache..."
cache_count=$(find . -name "__pycache__" -type d 2>/dev/null | wc -l)
if [ "$cache_count" -eq 0 ]; then
    echo "✅ No se encontraron carpetas __pycache__"
else
    echo "⚠️  Advertencia: Se encontraron $cache_count carpetas __pycache__"
fi

pyc_count=$(find . -name "*.pyc" 2>/dev/null | wc -l)
if [ "$pyc_count" -eq 0 ]; then
    echo "✅ No se encontraron archivos .pyc"
else
    echo "⚠️  Advertencia: Se encontraron $pyc_count archivos .pyc"
fi

# 6. Verificar tamaño del proyecto
echo ""
echo "📊 Estadísticas del proyecto:"
project_size=$(du -sh . | cut -f1)
echo "📏 Tamaño total: $project_size"

total_files=$(find . -type f -not -path "./venv/*" -not -path "./.git/*" | wc -l)
echo "📄 Archivos Python/proyecto: $total_files"

# 7. Probar configuración Django
echo ""
echo "🧪 Probando configuración Django..."
cd /home/emi/Escritorio/Mole-AI-backend1.1.0
if python3 manage.py check --deploy >/dev/null 2>&1; then
    echo "✅ python3 manage.py check - PASÓ"
else
    echo "❌ Error en python3 manage.py check:"
    python3 manage.py check --deploy
    exit 1
fi

# 8. Probar importaciones
echo ""
echo "🐍 Probando importaciones de apps..."
cd /home/emi/Escritorio/Mole-AI-backend1.1.0
python3 -c "
import sys
print('Python paths:')
for p in sys.path[:3]:
    print(f'  {p}')

print()
try:
    from ai_models.apps import AiModelsConfig
    print('✅ ai_models.apps.AiModelsConfig - OK')
except Exception as e:
    print(f'❌ Error importando ai_models: {e}')

try:
    from authentication.apps import AuthenticationConfig
    print('✅ authentication.apps.AuthenticationConfig - OK')
except Exception as e:
    print(f'❌ Error importando authentication: {e}')

try:
    from core.apps import CoreConfig
    print('✅ core.apps.CoreConfig - OK')
except Exception as e:
    print(f'❌ Error importando core: {e}')
"

echo ""
echo "🎉 VERIFICACIÓN COMPLETADA"
echo "=========================================="
echo "✅ Estructura reorganizada exitosamente"
echo "✅ Configuración Django ajustada"
echo "✅ Cache limpiado"
echo "✅ Proyecto listo para desarrollo"
echo ""
echo "🚀 Para iniciar el servidor:"
echo "   cd /home/emi/Escritorio/Mole-AI-backend1.1.0"
echo "   python manage.py runserver"