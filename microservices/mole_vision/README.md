# MS-1 Vision (Gatekeeper + TFLite)

Microservicio de visión que expone endpoints para inferencia con un modelo TFLite y actúa como gatekeeper para los diagnósticos.

Features:
- Inference con TFLite (MobileNet/Gatekeeper).
- Patrón Hexagonal: rutas delgadas (FastAPI) → caso de uso → puertos/implementaciones.
- Pydantic v2 DTOs para todos los contratos de datos (alta seguridad de tipos y rendimiento con Rust core).
- Modelo cargado una sola vez por proceso (patrón Singleton por ruta de modelo).

Requisitos (entorno aislado)
1. Crear/activar virtualenv en la raíz del repo:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

2. Instalar dependencias del microservicio:

```bash
pip install -r ms1_vision/requirements.txt
```

Ejecutar pruebas y smoke runner

- Test unitario del singleton:

```bash
pytest -q tests/test_singleton_vision_client.py::test_singleton_interpreter_used
```

- Smoke runner E2E (levanta internamente con TestClient y valida esquema Pydantic v2):

```bash
python3 tests/smoke_runner.py
```

Notas técnicas
- Los esquemas están en `ms1_vision/domain/schemas.py` y usan Pydantic v2 (`model_validate()`, `model_dump()`, `ConfigDict`).
- La carga del intérprete TFLite se realiza vía cache `_INTERPRETERS` en `ms1_vision/infrastructure/external/cnn_vision_client.py` — esto asegura que por cada `model_path` la instancia del intérprete se crea una sola vez por proceso, evitando fugas de memoria y sobrecarga por petición.
- En entornos CI/CD, las pruebas inyectan un `DummyInterpreter` para evitar la necesidad de `tflite-runtime` nativo y mantener determinismo.

Contacto
- Para más cambios relacionados con la integración del runtime nativo (build de la imagen con tflite-runtime adecuado), puedo preparar Dockerfiles de despliegue o instrucciones para el builder de la imagen.
