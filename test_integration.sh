#!/bin/bash

# Script de prueba para integración Django + FastAPI Phi-3.5
echo "🧪 Probando integración híbrida Django + FastAPI Phi-3.5..."

# Colores para output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}📋 Verificando servicios...${NC}"

# Verificar si Docker Compose está corriendo
if ! docker compose ps | grep -q "Up"; then
    echo -e "${RED}❌ Los servicios no están corriendo. Iniciando Docker Compose...${NC}"
    docker compose up -d postgres ai-vision-service django-backend
    sleep 30
fi

echo -e "${YELLOW}🔍 Test 1: Health check PostgreSQL${NC}"
if docker exec mole_ai_postgres_hex pg_isready -U mole_user -d mole_ai_db; then
    echo -e "${GREEN}✅ PostgreSQL OK${NC}"
else
    echo -e "${RED}❌ PostgreSQL Error${NC}"
    exit 1
fi

echo -e "${YELLOW}🔍 Test 2: Health check AI Service${NC}"
if curl -f http://localhost:8001/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ AI Service OK${NC}"
else
    echo -e "${RED}❌ AI Service Error${NC}"
    exit 1
fi

echo -e "${YELLOW}🔍 Test 3: Health check Django Backend${NC}"
if curl -f http://localhost:8002/admin/ > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Django Backend OK${NC}"
else
    echo -e "${RED}❌ Django Backend Error${NC}"
    exit 1
fi

echo -e "${YELLOW}🔍 Test 4: Migraciones Django${NC}"
if docker exec mole_ai_django_backend python manage.py migrate --check; then
    echo -e "${GREEN}✅ Migraciones OK${NC}"
else
    echo -e "${YELLOW}⚠️ Ejecutando migraciones...${NC}"
    docker exec mole_ai_django_backend python manage.py migrate
fi

echo -e "${YELLOW}🔍 Test 5: Comunicación Django → AI Service${NC}"
# Test de comunicación entre servicios
response=$(docker exec mole_ai_django_backend curl -s http://ai-vision-service:8000/health 2>/dev/null)
if [[ $response == *"healthy"* ]]; then
    echo -e "${GREEN}✅ Comunicación interna OK${NC}"
else
    echo -e "${RED}❌ Error comunicación interna${NC}"
    echo "Response: $response"
    exit 1
fi

echo -e "${YELLOW}🔍 Test 6: API Endpoints Django${NC}"
# Test endpoint de diagnóstico
test_payload='{"plant_id": 1, "imagen": "data:image/jpeg;base64,test", "sensores": {"ph": 6.5, "humedad": 65.0}}'
response=$(curl -s -X POST \
  -H "Content-Type: application/json" \
  -d "$test_payload" \
  http://localhost:8002/api/ai/diagnose/1/ 2>/dev/null)

if [[ $response == *"success"* ]] || [[ $response == *"error"* ]]; then
    echo -e "${GREEN}✅ API Django responde${NC}"
else
    echo -e "${RED}❌ API Django no responde${NC}"
    echo "Response: $response"
fi

echo -e "${YELLOW}🔍 Test 7: Crear superusuario Django${NC}"
# Crear superusuario si no existe
docker exec mole_ai_django_backend python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@mole-ai.com', 'admin123')
    print('Superusuario creado')
else:
    print('Superusuario ya existe')
" 2>/dev/null

echo -e "${GREEN}🎉 Todos los tests completados!${NC}"
echo ""
echo -e "${YELLOW}📊 Resumen de servicios:${NC}"
echo -e "  • PostgreSQL: localhost:5432"
echo -e "  • AI Service (FastAPI + Phi-3.5): http://localhost:8001"
echo -e "  • Django Backend: http://localhost:8002"
echo -e "  • Django Admin: http://localhost:8002/admin/"
echo ""
echo -e "${YELLOW}🔑 Credenciales:${NC}"
echo -e "  • Usuario: admin"
echo -e "  • Password: admin123"
echo ""
echo -e "${GREEN}✅ Arquitectura híbrida lista para usar!${NC}"