#!/bin/bash
# Prueba de validación JWT: token válido vs inválido.
set -e

echo "=== Test: Validación JWT ==="

# 1. Token inválido debe dar 401
echo "  Probando token inválido ..."
STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X POST http://localhost:8002/api/v1/mole-ai/chat \
    -H "Authorization: Bearer token-invalido" \
    -H "Content-Type: application/json" \
    -d '{"user_id":"test","message":"hola"}')
[ "$STATUS" = "401" ] || { echo "FAIL: Se esperaba 401, obtuvo $STATUS"; exit 1; }
echo "  ✅ Token inválido → 401"

# 2. Token válido debe pasar
echo "  Probando token válido ..."
JWT_TOKEN=$(python3 -c "
import jwt, time
payload = {'sub': 'test-user-002', 'aud': 'authenticated', 'exp': int(time.time()) + 3600}
print(jwt.encode(payload, 'test-secret-key-for-e2e-tests', algorithm='HS256'))
")
STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X POST http://localhost:8002/api/v1/mole-ai/chat \
    -H "Authorization: Bearer $JWT_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"user_id":"test-user-002","message":"hola"}')
[ "$STATUS" != "401" ] || { echo "FAIL: Token válido rechazado"; exit 1; }
echo "  ✅ Token válido aceptado (status $STATUS)"

echo "✅ Test JWT pasado exitosamente"
