#!/bin/bash
echo "🔍 Iniciando Auditoría SBOM (Software Bill of Materials)..."
echo "📦 Objetivo: Detectar licencias virales (GPL/AGPL) en microservicios."

audit_container() {
    CONTAINER=$1
    echo "------------------------------------------------"
    echo "🔎 Auditando contenedor: $CONTAINER"
    
    # Instalamos usando root (-u 0) para saltar bloqueos de permisos
    docker exec -u 0 $CONTAINER pip install -q pip-licenses
    
    # Ejecutamos a través de python -m para evadir el problema del $PATH
    docker exec -u 0 $CONTAINER python -m piplicenses --fail-on="GPL;AGPL;LGPL" --summary
    
    if [ $? -eq 0 ]; then
        echo "✅ $CONTAINER: LIMPIO de licencias virales."
    else
        echo "❌ $CONTAINER: ¡ALERTA! Licencia restrictiva detectada o error de ejecución."
    fi
}

# Auditamos los 3 motores principales
audit_container "django-backend"
audit_container "ms2_chat"
audit_container "ms1_vision"

echo "------------------------------------------------"
echo "🏁 Auditoría SBOM finalizada."
