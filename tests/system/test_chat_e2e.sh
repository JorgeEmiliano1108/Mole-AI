#!/bin/bash
# Prueba end-to-end del flujo de chat con datos reales en Redis + pgvector.
set -e

echo "=== Test: Chat E2E con sensores reales ==="

# 1. Generar token JWT HS256 (misma secret que en docker-compose.test.yml)
echo "  Generando token JWT ..."
JWT_TOKEN=$(python3 -c "
import jwt, time
payload = {
    'sub': 'test-user-001',
    'aud': 'authenticated',
    'exp': int(time.time()) + 3600,
    'iat': int(time.time())
}
print(jwt.encode(payload, 'test-secret-key-for-e2e-tests', algorithm='HS256'))
")
echo "  Token generado: ${JWT_TOKEN:0:20}..."

# 2. Insertar datos de sensores en Redis (simulando edge_node)
echo "  Insertando datos de sensor en Redis ..."
docker exec mole_e2e_redis redis-cli SET "sensor:test-user-001" '{"temp":28.5,"humidity":65,"uv":5}'
SENSOR_CHECK=$(docker exec mole_e2e_redis redis-cli GET "sensor:test-user-001")
echo "  Sensor data: $SENSOR_CHECK"

# 3. Enviar mensaje al chat
echo "  Enviando consulta al chat ..."
RESPONSE=$(curl -s -X POST http://localhost:8002/api/v1/mole-ai/chat \
    -H "Authorization: Bearer $JWT_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
        "user_id": "test-user-001",
        "message": "¿Cómo está mi cultivo hoy?",
        "session_id": "e2e-test-session"
    }')

echo "  Respuesta: $RESPONSE"

# 4. Validar que la respuesta contiene campo "respuesta" no vacío
echo "$RESPONSE" | python3 -c "
import sys, json
data = json.load(sys.stdin)
assert 'respuesta' in data, 'Falta campo respuesta'
assert len(data['respuesta']) > 0, 'Respuesta vacía'
print(f'  ✅ Respuesta contiene {len(data[\"respuesta\"])} caracteres')
"

# 5. Validar que el disclaimer esté presente
echo "$RESPONSE" | python3 -c "
import sys, json
data = json.load(sys.stdin)
assert data.get('disclaimer', ''), 'Falta disclaimer'
print('  ✅ Disclaimer presente')
"

echo "✅ Test Chat E2E pasado exitosamente"
