# Mole Vision API Reference

## Endpoints

### POST /api/v1/vision/analyze
Analiza una imagen de planta y retorna el diagnóstico.

**Autenticación**: Bearer token JWT requerido.

**Request**:
- Content-Type: multipart/form-data
- Body: file (imagen)

**Response**:
```json
{
  "id": "string",
  "plant_id": "string",
  "species": "string",
  "condition": "string",
  "condition_category": "HEALTHY|DISEASE|NUTRIENT_DEFICIENCY|PEST|ENVIRONMENTAL_STRESS|UNKNOWN",
  "severity": "LOW|MEDIUM|HIGH|CRITICAL",
  "confidence": 0.95,
  "ph_predicted": 6.5,
  "timestamp": "2024-01-01T00:00:00"
}
```

### POST /api/v1/vision/analyze-ph-strip
Analiza una tira reactiva de pH.

**Request**:
- Content-Type: multipart/form-data
- Body: file (imagen de tira reactiva)

**Response**:
```json
{
  "estimated_ph": 6.5,
  "method": "Colorimetry_Euclidean_RGB"
}
```

### GET /api/v1/vision/health
Health check básico.

### GET /api/v1/vision/healthz
Health check completo con verificación de componentes (modelo y Redis).

## Configuración

El servicio usa las siguientes variables de entorno:

- `SUPABASE_URL`: URL de Supabase
- `SUPABASE_JWT_SECRET`: Secret para validar JWTs
- `REDIS_URL`: URL de Redis
- `CNN_MODEL_PATH`: Ruta al modelo TFLite
- `ORIGEN_PERMITIDO`: Orígenes CORS permitidos