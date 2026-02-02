# 🌱 Mole AI - Guía de Implementación Híbrida Django + FastAPI Phi-3.5

## 📋 Arquitectura Implementada

Hemos exitosamente implementado una arquitectura híbrida donde:

- **Django** sirve como backend principal con CRUD, Admin panel, y autenticación
- **FastAPI + Phi-3.5** funciona como microservicio de IA consumido por Django
- **PostgreSQL** como base de datos compartida
- **Comunicación HTTP** entre Django → FastAPI para procesamiento de IA

## 🚀 Puesta en Marcha Rápida

### 1. Iniciar Servicios

```bash
# Iniciar todos los servicios
docker-compose up -d

# Iniciar servicios específicos
docker-compose up -d postgres ai-vision-service django-backend
```

### 2. Verificar Integración

```bash
# Ejecutar script de pruebas
./test_integration.sh
```

### 3. Acceder a los Servicios

- **Django Admin**: http://localhost:8002/admin/
  - Usuario: `admin`
  - Password: `admin123`

- **AI Service (FastAPI)**: http://localhost:8001/docs
- **Django API**: http://localhost:8002/api/ai/

## 📊 Estructura de Proyectos

```
Mole-AI/
├── backend_django/           # Backend Django principal
│   ├── ai_integration/       # App de integración IA
│   ├── plants_mgmt/          # Gestión de plantas
│   ├── diagnostics_mgmt/     # Gestión de diagnósticos
│   └── config/               # Configuración Django
├── ai_vision_service/        # Microservicio FastAPI + Phi-3.5
├── docker-compose.yml        # Configuración híbrida
└── test_integration.sh       # Script de pruebas
```

## 🔧 Endpoints Principales

### Django Backend

#### Gestión de Plantas
- `GET /api/plants/` - Listar plantas
- `POST /api/plants/` - Crear planta
- `GET /api/plants/{id}/` - Detalle planta
- `PUT /api/plants/{id}/` - Actualizar planta

#### Integración IA
- `POST /api/ai/diagnose/{plant_id}/` - Diagnosticar planta
- `POST /api/ai/batch-diagnose/` - Diagnóstico por lotes
- `GET /api/ai/health/` - Health check servicio IA
- `GET /api/ai/dashboard/` - Dashboard de IA

#### Chat con IA
- `POST /api/ai/chat/` - Chat sobre plantas

### AI Service (FastAPI)

- `POST /diagnostico` - Procesamiento con Phi-3.5
- `GET /health` - Health check
- `GET /system/metrics` - Métricas del sistema

## 🏗️ Flujo de Trabajo

1. **Usuario** interactúa con **Django Admin** o **API Django**
2. **Django** recibe solicitud (imagen + datos sensores)
3. **Django** envía HTTP request a **FastAPI AI Service**
4. **FastAPI** procesa con **Phi-3.5 Vision-Instruct**
5. **FastAPI** retorna diagnóstico a **Django**
6. **Django** guarda en base de datos y responde al usuario

## 🧪 Tests y Validación

### Comprobar Comunicación

```bash
# Test health check AI service
curl http://localhost:8001/health

# Test health check Django
curl http://localhost:8002/admin/

# Test comunicación interna (desde container Django)
docker exec mole_ai_django_backend curl http://ai-vision-service:8000/health
```

### Probar Diagnóstico

```bash
# Test endpoint diagnóstico
curl -X POST http://localhost:8002/api/ai/diagnose/1/ \
  -H "Content-Type: application/json" \
  -d '{"plant_id": 1, "imagen": "data:image/jpeg;base64,test", "sensores": {"ph": 6.5}}'
```

## 📈 Monitoreo

### Métricas Django
- Requests al servicio IA
- Tiempos de procesamiento
- Tasas de error

### Métricas AI Service  
- Uso de Phi-3.5
- Tiempos de inferencia
- Recursos del sistema

## 🛠️ Configuración

### Variables de Entorno

```bash
# Django
DEBUG=false
SECRET_KEY=your-secret-key
DATABASE_URL=postgresql://user:pass@postgres:5432/db
AI_SERVICE_URL=http://ai-vision-service:8000

# AI Service
MODEL_NAME=microsoft/Phi-3.5-vision-instruct
POSTGRES_HOST=postgres
```

### Base de Datos

La base de datos PostgreSQL es compartida entre ambos servicios:

- **Django**: Tablas de CRUD, usuarios, plantas
- **FastAPI**: Logs de IA, métricas (opcional)

## 🔄 Escalabilidad

### Horizontal Scaling
- Multiple instancias de Django
- Multiple instancias de AI Service
- Load balancer con Nginx

### Vertical Scaling
- More RAM/CPU para Phi-3.5
- GPU support para inferencia
- Optimización de modelos

## 🐛 Troubleshooting

### Problemas Comunes

1. **AI Service no responde**
   ```bash
   docker logs mole_ai_vision_service
   ```

2. **Django no conecta a AI Service**
   ```bash
   docker exec mole_ai_django_backend ping ai-vision-service
   ```

3. **Problemas con base de datos**
   ```bash
   docker exec mole_ai_postgres_hex pg_isready
   ```

### Logs

```bash
# Logs Django
docker logs mole_ai_django_backend

# Logs AI Service  
docker logs mole_ai_vision_service

# Logs PostgreSQL
docker logs mole_ai_postgres_hex
```

## 🎯 Próximos Pasos

1. **Frontend**: React/Vue.js app consumiendo Django API
2. **Autenticación**: JWT tokens para API endpoints
3. **Caching**: Redis para respuestas frecuentes
4. **Monitoring**: Prometheus + Grafana
5. **Testing**: Unit tests + integration tests
6. **Documentation**: OpenAPI/Swagger documentation

## ✅ Validación Final

Para confirmar que todo funciona correctamente:

1. ✅ Ejecutar `./test_integration.sh`
2. ✅ Acceder a http://localhost:8002/admin/
3. ✅ Crear una planta desde Django Admin
4. ✅ Probar diagnóstico con imagen de muestra
5. ✅ Verificar resultados en base de datos

**¡Arquitectura híbrida lista para producción!** 🚀