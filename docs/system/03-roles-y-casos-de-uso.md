# Roles y casos de uso

## Propósito
Definir los roles de usuario y los casos de uso principales que el sistema MOLE‑AI soporta, estableciendo claramente las responsabilidades, permisos, alcance de datos y trazabilidad a requisitos y pruebas.

## Roles del sistema
| Rol | Descripción funcional | Capacidades permitidas | Recursos (endpoints / UI) | Restricciones | Nivel de confianza / Alcance de datos |
|-----|-----------------------|-----------------------|--------------------------|----------------|----------------------------------------|
| **Superuser** | Usuario con privilegios máximos del framework Django. | Acceso total a la base de datos, modificar cualquier recurso y configuraciones de infraestructura. | Todos los endpoints CRUD. | Ninguna. | Máximo (full‑access, puede ver y modificar cualquier dato). |
| **Administrador (admin / staff)** | Control total del sistema sobre recursos operacionales. | CRUD sobre usuarios, plantas, especies y configuración global (excepto variables `NVIDIA_*`). | Endpoints bajo `IsSuperuserOrReadOnly` (escritura) y `IsAuthenticated` (lectura). | No puede cambiar variables `NVIDIA_*` ni modificar código del repositorio; esas acciones son **Futuro / Fuera de alcance**. | Alto (puede leer/editar datos de todos los usuarios y recursos, sin acceso a variables de modelo). |
| **Usuario autenticado** (`role=user` en JWT) | Agricultor o técnico que utiliza los servicios. | Gestionar sus propias plantas, enviar telemetría, consultar IA, analizar imágenes, generar reportes. | Endpoints marcados con `IsAuthenticated`. | No puede crear/modificar usuarios, especies globales ni cambiar configuraciones del sistema. | Medio (solo datos propios y recursos a los que está autorizado). |
| **Dispositivo IoT / Hardware** | Credencial de hardware asociada a un ESP32. | Enviar lecturas de sensores mediante endpoints de telemetría. | `POST /api/v1/sensor-data/*`, `PATCH …` mediante `HardwareOnlyPermission`. | Sólo opera sobre su propio `device_id`. | Bajo (acceso restringido a sus propios datos de sensor). |
| **Usuario anónimo** | Visitante sin autenticación. | Buscar especies públicas, registrarse y autenticarse. | Rutas `AllowAny` (registro, login, búsqueda pública). | No puede acceder a recursos protegidos ni enviar telemetría. | Ninguno (sin acceso a datos protegidos). |

## Reglas de autorización
- **`IsAuthenticated`** protege todos los recursos que requieren un JWT válido.
- **`IsSuperuserOrReadOnly`** permite lecturas a cualquier usuario autenticado pero restringe escrituras a super‑users o staff.
- **`HardwareOnlyPermission`** garantiza que solo los dispositivos con la marca `is_hardware_device` pueden usar los endpoints de telemetría.
- **Mutua exclusión:** los endpoints de telemetría aceptan **solo** `HardwareOnlyPermission`; los usuarios autenticados no pueden utilizarlos y viceversa.
- **Rate‑limit** y **anti‑replay** se aplican a los endpoints de chat y telemetría respectivamente (ver requisitos RF‑08, RF‑05).

## Casos de uso backend (UC-*)

### UC-01 Iniciar sesión
**Objetivo:** Obtener un token JWT válido.
**Actor principal:** Usuario anónimo.
**Actores secundarios:** Ninguno.
**Precondiciones:** Usuario posee credenciales válidas.
**Disparador:** Solicitud `POST /api/v1/auth/login/`.
**Flujo principal:**
1. Cliente envía `username` y `password`.
2. Backend valida credenciales.
3. Se genera y devuelve JWT con claims `sub`, `username`, `email`, `role`, `exp`.
**Flujos alternos / excepciones:** Credenciales inválidas → `401 Unauthorized`; parámetros faltantes → `400 Bad Request`.
**Postcondiciones:** Cliente posee token JWT válido.
**Requisitos relacionados:** RF-01.
**Endpoint / UI involucrada:** `POST /api/v1/auth/login/`.
**Evidencia de verificación:** `test_login_dual.py` (Automatizado).

### UC-02 Registrar usuario
**Objetivo:** Crear una cuenta de agricultor o técnico.
**Actor principal:** Usuario anónimo.
**Actores secundarios:** Ninguno.
**Precondiciones:** Ninguna.
**Disparador:** Solicitud `POST /api/v1/auth/register/`.
**Flujo principal:**
1. Cliente envía `username`, `password` y opcional `email`.
2. Sistema verifica fuerza de contraseña.
3. Se crea registro `User` con `is_email_verified=False`.
4. Se envía email de verificación (asíncrono).
**Flujos alternos / excepciones:** Usuario ya existe → `409 Conflict`.
**Postcondiciones:** Usuario creado y pendiente de verificación.
**Requisitos relacionados:** RF-01.
**Endpoint / UI involucrada:** `POST /api/v1/auth/register/`.
**Evidencia de verificación:** `test_user_registration.py` (Pendiente).

### UC-03 Consultar perfil
**Objetivo:** Obtener datos del perfil del usuario autenticado.
**Actor principal:** Usuario autenticado.
**Actores secundarios:** Ninguno.
**Precondiciones:** JWT válido.
**Disparador:** Solicitud `GET /api/v1/auth/profile/`.
**Flujo principal:** Backend devuelve JSON con información del usuario.
**Flujos alternos / excepciones:** Token expirado → `401 Unauthorized`.
**Postcondiciones:** Información de perfil entregada.
**Requisitos relacionados:** RF-03.
**Endpoint / UI involucrada:** `GET /api/v1/auth/profile/`.
**Evidencia de verificación:** `test_user_profile.py` (Automatizado).

### UC-04 Administrar usuarios
**Objetivo:** Crear, modificar o eliminar usuarios del sistema.
**Actor principal:** Administrador.
**Actores secundarios:** Superuser (permite todas las operaciones).
**Precondiciones:** JWT con rol `admin` o `superuser`.
**Disparador:** Acción administrativa en UI de gestión o vía API.
**Flujo principal:**
- Listado: `GET /api/v1/auth/users/`.
- Creación: `POST /api/v1/auth/users/`.
- Actualización: `PATCH /api/v1/auth/profile/`.
- Eliminación: `DELETE /api/v1/auth/profile/`.
**Flujos alternos / excepciones:** Intento de eliminar superuser → rechazo `403`.
**Postcondiciones:** Cambios de usuario reflejados en el sistema; registro de trazabilidad.
**Requisitos relacionados:** RF-02, RF-03.
**Endpoint / UI involucrada:** `/api/v1/auth/*`.
**Evidencia de verificación:** Pendiente

### UC-05 Gestionar colección de plantas
**Objetivo:** Listar, crear, actualizar o eliminar plantas asociadas al usuario.
**Actor principal:** Usuario autenticado.
**Actores secundarios:** Ninguno.
**Precondiciones:** JWT válido.
**Disparador:** Interacción con la UI de gestión de plantas o llamada API.
**Flujo principal:**
- Listado: `GET /api/v1/plants/my-collection/`.
- Creación: `POST /api/v1/user-plants/` con datos de la planta.
- Actualización: `PATCH /api/v1/plants/<uuid>/`.
- Eliminación: `DELETE /api/v1/plants/<uuid>/`.
**Flujos alternos / excepciones:** Plantas duplicadas → `409 Conflict`.
**Postcondiciones:** Plantas persistidas y vinculadas al usuario.
**Requisitos relacionados:** RF-04.
**Endpoint / UI involucrada:** `/api/v1/plants/*`.
**Evidencia de verificación:** Pendiente

### UC-06 Enviar telemetría IoT
**Objetivo:** Registrar datos de sensores en tiempo real.
**Actor principal:** Dispositivo IoT (hardware).
**Actores secundarios:** Ninguno.
**Precondiciones:** `auth_token` válido y asociado a `device_id`.
**Disparador:** Envío de lectura de sensor.
**Flujo principal:** `POST /api/v1/sensor-data/` con payload JSON.
**Flujos alternos / excepciones:** Violación de anti‑replay → `400 Bad Request`; exceso de velocidad → `429 Too Many Requests`.
**Postcondiciones:** Lectura de telemetría almacenada.
**Requisitos relacionados:** RF-05.
**Endpoint / UI involucrada:** `/api/v1/sensor-data/`.
**Evidencia de verificación:** `test_sensor_data.patch` (Automatizado).

### UC-07 Cargar documento PDF para conocimiento (RAG)
**Objetivo:** Enriquecer la base de conocimiento con información de documentos PDF.
**Actor principal:** Usuario autenticado.
**Actores secundarios:** Ninguno.
**Precondiciones:** JWT válido.
**Disparador:** Subida de archivo PDF vía UI o API.
**Flujo principal:** `POST /api/v1/knowledge/ingest-pdf` con archivo PDF.
**Flujos alternos / excepciones:** Archivo no PDF → `415 Unsupported Media Type`.
**Postcondiciones:** Documento indexado y disponible para RAG.
**Requisitos relacionados:** RF-06, RF-07.
**Endpoint / UI involucrada:** `/api/v1/knowledge/ingest-pdf`.
**Evidencia de verificación:** `test_pdf_ingest.py` (Pendiente).

### UC-08 Consultar agente IA (chat)
**Objetivo:** Obtener respuesta agronómica basada en contexto y conocimiento.
**Actor principal:** Usuario autenticado.
**Actores secundarios:** Ninguno.
**Precondiciones:** JWT válido; usuario tiene planta registrada.
**Disparador:** Envío de mensaje de chat.
**Flujo principal:** `POST /api/v1/mole-ai/chat` con mensaje y `user_id`.
**Flujos alternos / excepciones:** Mensaje que viola NOM‑059 → `403 Forbidden`.
**Postcondiciones:** Respuesta de chat devuelta.
**Requisitos relacionados:** RF-08.
**Endpoint / UI involucrada:** `/api/v1/mole-ai/chat`.
**Evidencia de verificación:** `test_chat_e2e.py` (Automatizado).

### UC-09 Analizar imagen (visión)
**Objetivo:** Generar diagnóstico de planta a partir de una fotografía.
**Actor principal:** Usuario autenticado.
**Actores secundarios:** Ninguno.
**Precondiciones:** JWT válido; imagen en formato soportado.
**Disparador:** Envío de imagen para análisis.
**Flujo principal:** `POST /api/v1/vision/analyze/` con `multipart/form-data`.
**Flujos alternos / excepciones:** Imagen corrupta → `400 Bad Request`.
**Postcondiciones:** Diagnóstico estructurado devuelto.
**Requisitos relacionados:** RF-09.
**Endpoint / UI involucrada:** `/api/v1/vision/analyze/`.
**Evidencia de verificación:** `test_vision_api.py` (Automatizado).

### UC-10 Generar reporte de sensores
**Objetivo:** Obtener un PDF consolidado de lecturas de sensores para un rango de tiempo.
**Actor principal:** Usuario autenticado.
**Actores secundarios:** Ninguno.
**Precondiciones:** JWT válido; parámetros `date_range_days` y lista de sensores.
**Disparador:** Solicitud de generación de reporte.
**Flujo principal:**
1. `POST /api/v1/reports/generate` inicia el procesamiento asíncrono del reporte.
2. El sistema genera el PDF y lo almacena en un repositorio temporal.
3. El usuario recibe un enlace temporal de descarga para obtener el reporte.
**Flujos alternos / excepciones:** Fallo en generación → `500 Internal Server Error`.
**Postcondiciones:** PDF disponible para descarga dentro del periodo de retención configurado.
**Requisitos relacionados:** RF-10.
**Endpoint / UI involucrada:** `/api/v1/reports/generate`.
**Evidencia de verificación:** `test_report_generation.py` (Automatizado).

### UC-11 Auditoría
**Objetivo:** Registrar eventos críticos del sistema para trazabilidad y cumplimiento.
**Actor principal:** Sistema (backend).
**Actores secundarios:** Administrador (visualiza auditoría).
**Precondiciones:** Operaciones CRUD realizadas.
**Disparador:** Acción que modifica datos sensibles (creación, actualización, eliminación).
**Flujo principal:** Registro automático de eventos críticos con información de usuario, timestamp, acción y objeto afectado.
**Flujos alternos / excepciones:** Fallo al escribir log → `500 Internal Server Error`.
**Postcondiciones:** Evento registrado y disponible para consultas.
**Requisitos relacionados:** RF-11.
**Endpoint / UI involucrada:** Proceso interno del sistema (sin endpoint público).
**Evidencia de verificación:** `test_audit.py` (Automatizado).

### UC-12 Gestionar configuración global (Futuro)
**Objetivo:** Permitir al administrador modificar variables de modelo (`NVIDIA_*`) y configuraciones de despliegue.
**Actor principal:** Administrador.
**Actores secundarios:** Ninguno.
**Precondiciones:** JWT con rol `admin`.
**Disparador:** Acceso a la sección de configuración en UI o API.
**Flujo principal:** (Futuro) UI/API para editar variables de entorno y reiniciar servicios.
**Flujos alternos / excepciones:** Intento sin permiso → `403 Forbidden`.
**Postcondiciones:** Configuración actualizada y aplicada tras reinicio.
**Requisitos relacionados:** RF-12 (Fuera de alcance actual).
**Endpoint / UI involucrada:** *Pendiente de definir*.
**Evidencia de verificación:** *Pendiente*.

## Casos de uso frontend (UC-F-*)
> Todos los casos frontend comparten Actor principal **Usuario autenticado** y Disparador **Interacción UI**. Se indica una única nota común para evitar repetición.

**Nota común:** Actor principal = Usuario autenticado; Disparador = interacción con la interfaz gráfica (click, input, etc.).

### UC-F-01 Interfaz de login
- **Objetivo:** Permitir al usuario autenticarse mediante UI.
- **Actores secundarios:** Ninguno.
- **Precondiciones:** Usuario anónimo visita la página de login.
- **Flujo principal:** UI captura `username`/`password` y llama a `POST /api/v1/auth/login/`.
- **Flujos alternos / excepciones:** Credenciales inválidas → mensaje de error.
- **Postcondiciones:** Usuario redirigido a dashboard con JWT almacenado.
- **Requisitos relacionados:** RF-F-01.
- **Endpoint / UI involucrada:** UI login (frontend).
- **Evidencia de verificación:** `test_ui_login.py` (Pendiente).

### UC-F-02 Navegación entre vistas
- **Objetivo:** Permitir al usuario moverse entre las diferentes vistas de la aplicación.
- **Actores secundarios:** Ninguno.
- **Precondiciones:** Usuario autenticado tiene acceso al dashboard.
- **Flujo principal:** UI muestra barra de navegación y rutas internas.
- **Flujos alternos / excepciones:** Acceso a vista no autorizada → redirección a error 403.
- **Postcondiciones:** Vista mostrada correctamente.
- **Requisitos relacionados:** RF-F-02.
- **Endpoint / UI involucrada:** UI navegación (frontend).
- **Evidencia de verificación:** `test_ui_navigation.py` (Pendiente).

### UC-F-03 Chat IA UI
- **Objetivo:** Interactuar con el agente de IA a través del chat visual.
- **Actores secundarios:** Ninguno.
- **Precondiciones:** Usuario autenticado accede a la vista de chat.
- **Flujo principal:** UI envía mensaje a `POST /api/v1/mole-ai/chat` y muestra respuesta.
- **Flujos alternos / excepciones:** Mensaje prohibido por NOM‑059 → aviso al usuario.
- **Postcondiciones:** Conversación mostrada en pantalla.
- **Requisitos relacionados:** RF-F-03.
- **Endpoint / UI involucrada:** UI chat (frontend).
- **Evidencia de verificación:** `test_ui_chat.py` (Pendiente).

### UC-F-04 Visión IA UI
- **Objetivo:** Enviar imagen para diagnóstico y visualizar resultados.
- **Actores secundarios:** Ninguno.
- **Precondiciones:** Usuario autenticado abre la vista de visión.
- **Flujo principal:** UI envía imagen a `POST /api/v1/vision/analyze/` y muestra diagnóstico.
- **Flujos alternos / excepciones:** Imagen no soportada → mensaje de error.
- **Postcondiciones:** Resultado mostrado al usuario.
- **Requisitos relacionados:** RF-F-04.
- **Endpoint / UI involucrada:** UI visión (frontend).
- **Evidencia de verificación:** `test_ui_vision.py` (Pendiente).

### UC-F-05 Generación y descarga de reportes UI
- **Objetivo:** Permitir al usuario solicitar y descargar reportes de sensores.
- **Actores secundarios:** Ninguno.
- **Precondiciones:** Usuario autenticado en vista de reportes.
- **Flujo principal:** UI llama a `POST /api/v1/reports/generate`, muestra progreso y descarga PDF.
- **Flujos alternos / excepciones:** Error en generación → notificación.
- **Postcondiciones:** PDF descargado o enlace disponible.
- **Requisitos relacionados:** RF-F-05.
- **Endpoint / UI involucrada:** UI reportes (frontend).
- **Evidencia de verificación:** `test_ui_report_download.py` (Pendiente).

### UC-F-06 Envío de telemetría manual UI
- **Objetivo:** Permitir al usuario ingresar lecturas de sensores manualmente.
- **Actores secundarios:** Ninguno.
- **Precondiciones:** Usuario autenticado en vista de telemetría.
- **Flujo principal:** UI permite captura manual; envío al endpoint de telemetría no está permitido para usuarios autenticados (pendiente de definición).
- **Flujos alternos / excepciones:** Datos fuera de rango → error de validación.
- **Postcondiciones:** Pendiente de definición: el almacenamiento de telemetría manual desde usuario autenticado no está especificado.
- **Requisitos relacionados:** RF-F-06.
- **Endpoint / UI involucrada:** UI telemetría (frontend).
- **Evidencia de verificación:** `test_ui_telemetry.py` (Pendiente).

## Matriz de trazabilidad de casos de uso
| Caso de uso | Rol principal | Requisito relacionado | Endpoint / UI | Estado | Test asociado |
|-------------|--------------|-----------------------|---------------|--------|--------------|
| UC-01 | Anónimo | RF-01 | POST /api/v1/auth/login/ | Implementado | test_login_dual.py |
| UC-02 | Anónimo | RF-01 | POST /api/v1/auth/register/ | Implementado | Pendiente |
| UC-03 | Usuario autenticado | RF-03 | GET /api/v1/auth/profile/ | Implementado | test_user_profile.py |
| UC-04 | Administrador | RF-02, RF-03 | /api/v1/auth/users/* | Implementado | Pendiente |
| UC-05 | Usuario autenticado | RF-04 | /api/v1/user-plants/* | Implementado | Pendiente |
| UC-06 | Hardware | RF-05 | POST /api/v1/sensor-data/ | Implementado | test_sensor_data.patch |
| UC-07 | Usuario autenticado | RF-06, RF-07 | POST /api/v1/knowledge/ingest-pdf | Implementado | Pendiente |
| UC-08 | Usuario autenticado | RF-08 | POST /api/v1/mole-ai/chat | Implementado | test_chat_e2e.py |
| UC-09 | Usuario autenticado | RF-09 | POST /api/v1/vision/analyze/ | Implementado | test_vision_api.py |
| UC-10 | Usuario autenticado | RF-10 | POST /api/v1/reports/generate | Implementado | test_report_generation.py |
| UC-11 | Sistema | RF-11 | Proceso interno del sistema (sin endpoint público) | Implementado | test_audit.py |
| UC-12 | Administrador | RF-12 (Futuro) | *Pendiente* | Futuro | Pendiente |
| UC-F-01 | Usuario autenticado | RF-F-01 | UI login (frontend) | Implementado | Pendiente |
| UC-F-02 | Usuario autenticado | RF-F-02 | UI navegación (frontend) | Parcial | Pendiente |
| UC-F-03 | Usuario autenticado | RF-F-03 | UI chat (frontend) | Implementado | Pendiente |
| UC-F-04 | Usuario autenticado | RF-F-04 | UI visión (frontend) | Parcial | Pendiente |
| UC-F-05 | Usuario autenticado | RF-F-05 | UI reportes (frontend) | Parcial | Pendiente |
| UC-F-06 | Usuario autenticado | RF-F-06 | UI telemetría (frontend) | Parcial | Pendiente |

## Referencias cruzadas
- Cada caso de uso incluye el ID de requisito correspondiente que se verifica contra la matriz de trazabilidad en **02‑requisitos.md**.
- Los requisitos marcados como *Fuera de alcance actual* aparecen en la tabla con estado **Futuro** y sin pruebas asociadas.
