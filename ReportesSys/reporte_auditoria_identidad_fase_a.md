# Reporte de Auditoría: Gestión de Identidad y Seguridad IoT (Candado)

**Fecha:** 2026-03-08  
**Autor:** GitHub Copilot — Senior Django Developer & Security Architect  
**Alcance:** FASE A — Activación de Gestión de Identidad, Autenticación Híbrida y Blindaje de Ingesta M2M.  

---

## 1. Resumen Ejecutivo

Este reporte detalla el análisis de la infraestructura de backend orientada a habilitar la operación para usuarios reales, permitiendo escalar a entornos de producción. La buena noticia es que **la mayor parte del ecosistema ya fue provisionado y desarrollado con éxito previamente**. La tarea principal consiste en conectar estas piezas, certificar los contratos y asegurar el endpoint crítico de telemetría implementando un "Candado IoT".

---

## 2. Estado de Autenticación Híbrida (Confirmado ✅)

El sistema de autenticación de "Mole.AI" maneja actualmente un enfoque dual seguro:

1. **Usuarios y App Móvil/Web (Supabase JWT):** 
   - Implementado en `apps/authentication/infrastructure/authentication.py`.
   - La clase `SupabaseAuthentication` valida en tiempo real los tokens de Bearer empleando JWKS públicos desde Supabase.
   - Está correctamente integrada con la tabla `auth_user` de Django. Registra a los usuarios "al vuelo" si no existen en la BD.
   - El sistema en general está protegido de manera predeterminada a través de `REST_FRAMEWORK['DEFAULT_AUTHENTICATION_CLASSES']`.

2. **Dispositivos IoT (Hardware API Key):**
   - Implementado para ESP32 y Edge Nodes en `HardwareAPIKeyAuthentication`.
   - Utiliza exclusivamente cabeceras cifradas de M2M (`X-Hardware-Api-Key`).

**Veredicto:** El esquema es sólido, sigue las mejores prácticas (Arquitectura Zero-Trust) y no necesita re-escritura.

---

## 3. Infraestructura del CRUD de Plantas (`apps.plants`) (Confirmado ✅)

Se auditó el módulo responsable de relacionar a los usuarios con el hardware mediante los `plant_id` (UUIDs).

- **Asignación a BD:** El modelo `UserPlant` se encuentra listo y mapea directamente a la tabla `user_plants` en Supabase de forma no administrada (`managed=False`).
- **Serializadores y Vistas:** Se encuentran estructurados de forma semántica en `apps/plants/presentation/serializers.py` y `apps/plants/presentation/views.py`.
- **Endpoints disponibles y funcionales:**
  - `POST /api/v1/plants/`: Registra y genera una nueva planta en el perfil del usuario (retornando el UUID para configurar el hardware).
  - `GET /api/v1/plants/`: Solicita la lista privada de las plantas del agricultor actual.

**Acciones preventivas / Oportunidad de mejora:**
La aplicación modular no cuenta con su respectivo `admin.py`. Se recomienda crearlo para registrar `UserPlant`, permitiendo al equipo de soporte de Nivel 1 administrar o diagnosticar los vínculos hardware/usuario desde la consola de administración de Django.

---

## 4. Parche de Seguridad Crítico: El "Candado IoT" (Requiere Acción ⚠️)

La auditoría en la capa de endpoints de Ingesta (`apps/core/presentation/views.py` -> `sensor_data_view` y `sensor_batch_view`) revela que el control de asociación existe estructuralmente, pero bajo un estatus HTTP semánticamente débil e inseguro para M2M.

**Hallazgo:**
Si un dispositivo (ESP32 / Edge Node) inyecta datos con un API Key Válido, pero utiliza un `plant_id` UUID que **no** existe en la tabla `user_plants`, el ecosistema lo rechaza retornando un **`HTTP 404 NOT FOUND`**.

**Riesgo de Seguridad:**
Devolver un `404` ante una petición con credenciales (Hardware API Key) pero un recurso inválido revela información de topología a posibles atacantes en redes. Indica "El endpoint existe, el API Key funcionó, pero el ID del recurso que intentaste inyectar no". 

**Refactorización Propuesta:**
El endpoint debe implementar el "Candado IoT" y denegar cualquier intento de inyección de recursos no provisionados devolviendo **`HTTP 403 FORBIDDEN`**. El mensaje debe ser ambiguo para scanners: `"plant_id no registrado o acceso no autorizado"`. 

### Snippets de Solución a Inyectar:

Para `sensor_data_view` (~ Línea 80-85):
```python
    if not UserPlant.objects.filter(id=data['plant_id']).exists():
        return Response(
            {"error": "plant_id no registrado o acceso no autorizado",
             "detail": "El plant_id no existe en user_plants o no está asociado a una cuenta activa."},
            status=status.HTTP_403_FORBIDDEN,  # Modificado de 404 a 403
        )
```

Para `sensor_batch_view` (~ Línea 140-145):
```python
    unknown_ids = batch_plant_ids - existing_ids
    if unknown_ids:
        return Response(
            {"error": "plant_id(s) no registrados protegidos por candado IoT",
             "unknown_plant_ids": [str(uid) for uid in unknown_ids]},
            status=status.HTTP_403_FORBIDDEN,  # Modificado de 404 a 403
        )
```

---

## 5. Planes Futuros y Next Steps

1. **Parcheo de Core Views:** Ejecutar el `multi_replace` en `apps/core/presentation/views.py` para aplicar las políticas `HTTP_403_FORBIDDEN`.
2. **Actualización de Test Suites:** Escribir los tests de regresión (`test_sensor_data_m2m_rejects_unregistered_plant_id` y su versión Batch) en `tests/integration/test_m2m_ingest_wide_table.py` garantizando un retorno 403 sobre UUIDs falsos.
3. **Registro en Admin:** Añadir la visualización de `UserPlant` al panel de control de Django.
