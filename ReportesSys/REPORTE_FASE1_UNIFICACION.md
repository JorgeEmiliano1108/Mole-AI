# Reporte de Implementación: Fase 1 - Unificación de Base de Datos y Endpoints REST

**Fecha:** 14 de Marzo de 2026  
**Contexto:** Ejecución del Roadmap de Mole.AI (Paso 1)

## 1. Sincronización DB y Unificación de Modelos (Django -> Supabase)
Se auditó y corrigió la discrepancia estructural crítica que existía entre los modelos de Django y el esquema SQL real de Supabase. Permitimos que Django retome el control quitando el flag restrictivo.

- **`SensorLog`**: Retirado el campo `ph_level` ya que no existía en el esquema de la tabla wide-table de Supabase.
- **`UserPlant`**: Reemplazados los campos `name`, `location` por `nickname` y el ForeignKey `species_id` para coincidir 1:1 con la BD de producción.
- **`AIDiagnostic`**: Reestructurado con los campos reales (`analyzed_at`, `image_path`, `diagnosis_label`, `confidence_score`, `metadata`).
- **`BotanicalKnowledge`**: Nuevo modelo que reemplaza al antiguo `PlantKnowledge`, reflejando exactamente la tabla y tipo vectorial para el RAG.
- **Cambio de Estado**: Se eliminó `managed = False` en favor de `managed = True` para todas las entidades centralizadas.

## 2. Refactorización de Arquitectura de Rutas (Deuda Técnica)
Se resolvió la deuda técnica detectada en el mecanismo de enrutamiento aislado y hardcodeado que introducía código espagueti.

- Centralización del prefijo `api/v1/` estructurado nativamente en `mole_ai_backend/urls.py`.
- Refactorización de los archivos locales de rutas (`core/presentation/urls.py`, `authentication/...`, `plants/...`, `ai_models/...`) para eliminar los paths absolutos, permitiendo una inclusión modular e inyección de middlewares general izados de DRF.

## 3. Desarrollo de Funcionalidades (Endpoints Móviles)
Agregamos los requerimientos REST finales estipulados para habilitar a los equipos Front-End y Móvil, con protección de JSON Web Tokens (JWT).

- **Historial Consolidado (`GET /api/v1/history/`)**: 
  - Vista agregada: `consolidated_history_view` (Fusiona telemetría `SensorLog` y `AIDiagnostic` ordenados cronológicamente).
  - Resiliencia: Integra una clase estándar basada en `PageNumberPagination` (limita las queries en lotes de 50, con tope máximo de 1000) previniendo caídas del API por el alto volumen emitido por los ESP32.
- **Sistema de Favoritos (`GET/POST /api/v1/plants/favorites/`)**: 
  - Nuevos serializers (`FavoritePlantSerializer`) y vistas dedicadas a la gestión CRUD de las plantas favoritas de cada granjero.

## 4. Estrategia de Despliegue Habilitada: Migración Fake-Híbrida
Para prevenir el colapso del cluster PostgreSQL en Supabase por el error `ProgrammingError: relation already exists`, se diseñó y dejó el entorno listo para la **Migración Híbrida**.

- Se ocultó (comentó) temporalmente de manera intencional el modelo `FavoritePlant`.
- **Hoja de Ruta de Terminal requerida:**
  1. `python manage.py makemigrations core plants`
  2. `python manage.py migrate core --fake-initial`
  3. `python manage.py migrate plants --fake-initial`
  4. Quitar el comentario a `FavoritePlant` en `models.py`.
  5. `python manage.py makemigrations plants` && `python manage.py migrate plants`.