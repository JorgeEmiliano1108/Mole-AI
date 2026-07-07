#!/bin/bash
set -e

echo "=== Esperando health checks de servicios ==="

# Verificar contenedores de infraestructura
for container in mole_e2e_postgres mole_e2e_redis mole_e2e_nim_fake mole_e2e_minio; do
    echo "  Esperando contenedor $container ..."
    until docker inspect -f '{{.State.Status}}' "$container" 2>/dev/null | grep -q "running"; do
        sleep 2
    done
    echo "  ✅ $container running"
done

# Verificar health checks HTTP
echo "  Esperando ms2_chat (http://localhost:8002/api/v1/health) ..."
until curl -s -f http://localhost:8002/api/v1/health > /dev/null 2>&1; do
    sleep 2
done
echo "  ✅ ms2_chat OK"

echo "  Esperando ms3_reports (http://localhost:8003/health) ..."
until curl -s -f http://localhost:8003/health > /dev/null 2>&1; do
    sleep 2
done
echo "  ✅ ms3_reports OK"

# ms1_vision has a pre-existing opentelemetry dependency issue; optional for mole_chat tests
if curl -s -f http://localhost:8001/api/v1/vision/health/ > /dev/null 2>&1; then
    echo "  ✅ ms1_vision OK"
else
    echo "  ⚠️  ms1_vision SKIPPED (opentelemetry not available)"
fi

echo ""
echo "✅ Todos los servicios listos"
