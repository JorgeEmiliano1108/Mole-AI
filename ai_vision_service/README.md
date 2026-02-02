# Mole AI Vision Service

Servicio FastAPI con arquitectura hexagonal para análisis de imágenes de plantas usando YOLOv8.

## Arquitectura

```
domain/           # Lógica de negocio pura
├── models.py     # Modelos de dominio
└── exceptions.py # Excepciones específicas

ports/            # Interfaces (contratos)
├── input.py      # Puertos de entrada
└── output.py     # Puertos de salida

adapters/         # Implementaciones de infraestructura
├── inbound/      # API REST (FastAPI)
└── outbound/     # YOLO, almacenamiento

use_cases/        # Casos de uso de negocio
config/           # Configuración
```

## Instalación

```bash
# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# o
venv\Scripts\activate     # Windows

# Instalar dependencias
pip install -r requirements.txt
```

## Ejecución

```bash
python main.py
```

El servicio estará disponible en `http://localhost:8001`

## Endpoints

- `POST /api/v1/analyze` - Analizar imagen (base64)
- `POST /api/v1/analyze/upload` - Analizar imagen (archivo)
- `POST /api/v1/detect-plant` - Detectar tipo de planta
- `GET /health` - Verificación de salud

## Variables de Entorno

Copiar `.env.example` a `.env` y configurar:

- `VISION_SERVICE_HOST` - Host del servicio (default: 0.0.0.0)
- `VISION_SERVICE_PORT` - Puerto del servicio (default: 8001)
- `IMAGE_STORAGE_PATH` - Ruta de almacenamiento de imágenes
- `MODEL_CONFIDENCE_THRESHOLD` - Umbral de confianza para detecciones

## Tipos de Análisis

- `infrared` - Análisis de estrés hídrico con imágenes NoIR
- `rgb` - Detección de plagas y enfermedades con imágenes RGB