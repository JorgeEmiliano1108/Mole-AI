# Contrato móvil — Mole.AI API v1 para Flutter (APK)

> Fuente de verdad: código (`core_backend/`) + snapshot `docs/contracts/openapi.yml`
> (generado con `manage.py spectacular`, 76 paths v1 + `/api/schema/`, 2026-09-17).
> Toda afirmación cita `ruta:línea`. Si el schema y este documento divergen, manda el código
> y el gate CI `schema-diff` falla (ver §11).
> Decisión usuario 2026-09-17: visión **async vía Django+Celery**, chat **vía gateway**,
> MVP recortado = **auth + especies + telemetría + visión** (chat/mapa/reportes = fase 2).

## 0. Base

- Base URL: `https://<host>/api/v1/` (solo HTTPS en prod; `http` únicamente para setup local).
- Trailing slash obligatorio (`APPEND_SLASH=True` por defecto Django; el gateway NO redirige POST sin `/` de forma fiable → el cliente siempre envía `/` final).
  Excepción documentada: estos paths del backend **no** llevan `/` final
  (`core/urls.py:22,57-66`) y el cliente los usa tal cual los declara el snapshot:
  `sensors/ingest`, `admin/statistics`, `admin/report-text`, `admin/live-alerts`,
  `admin/reports/generate`, `admin/reports/<job>/status`, `reports/users`, `reports/plants`.
  Ninguno pertenece al MVP (admin/M2M/fase 2).
- JSON `Content-Type: application/json` salvo uploads (`multipart/form-data`).
- Timeouts: 30s general, 120s IA (precedente `ApiService.js:11` `_aiEndpoints`).
- Auth: `Authorization: Bearer <JWT>` en todo endpoint `IsAuthenticated`.

## 1. Auth — `apps/authentication/`

| Método + path | Request | Response | Código |
|---|---|---|---|
| `POST auth/login/` (`AllowAny`, Axes: 5 fallos → bloqueo 1h, `settings.py:188-193`) | `{username, password}` (`username` admite email con `@`, `views.py:252-267`) | `200 {token, role}` (`role=user\|admin\|superuser`, `views.py:276-309`); `400 {error}` sin campos; `401 {error:"Credenciales inválidas."}` | `authentication/views.py:239-309` |
| `POST auth/register/` (`AllowAny`, LFPDPPP Art. 8: exige `consent:true`, 400 si falta) | `{username, password, email?, consent:true}` | `201 {status:created, username, email_verification_required:true}` + `AuditLog CONSENT_GRANTED` + mail Celery | `authentication/views.py:184-236`, `consent.py:record_consent` |
| `POST auth/refresh/` (requiere Bearer **vigente** + `LocalJWTAuthentication`) | — (header) | `200 {token}` (nuevo JWT mismo schema; stateless, ventana deslizante 20min) | `authentication/refresh.py:14-44` |
| `POST auth/logout/` | — | `200 {status:logged_out}` + **revocación servidor**: el `jti` se publica en denylist (Redis/locmem) con TTL = vida restante → el token viejo responde 401. El APK además borra secure storage | `authentication/views.py:logout_view`, `token_denylist.py` |
| `POST auth/password-reset/request/` (`AllowAny`, throttle anon, siempre 202 anti-enumeración) | `{email}` | `202 {status:accepted}` + mail token un solo uso TTL 1h + `AuditLog PASSWORD_RESET_REQUESTED` (solo si el email existe; indistinguible si no) | `authentication/views.py:password_reset_request_view`, ADR-0006 |
| `POST auth/password-reset/confirm/` (`AllowAny`) | `{token, new_password}` (+fortaleza NIST) | `200 {status:password_updated}` + invalida token + `AuditLog PASSWORD_RESET_CONFIRMED`; `400` token inválido/expirado/debil | `authentication/views.py:password_reset_confirm_view` |
| `POST auth/password-change/` (`IsAuthenticated`) | `{current_password, new_password}` | `200 {status:password_updated}` + `AuditLog PASSWORD_CHANGED`; `400` actual incorrecta/debil | `authentication/views.py:password_change_view` |
| `POST auth/consent/` (LFPDPPP) | `{consent: true\|false}` estricto (`400` si no booleano) | `200 {status:recorded, data_consent, data_consent_date}` + `AuditLog(CONSENT_GRANTED\|REVOKED)` | `authentication/views.py:97-128` |
| `GET/PATCH/DELETE auth/profile/` | — / parcial / — | `{id,email,full_name,first_name,last_name,avatar_url?,phone_number?,user_id,role,data_consent,data_consent_date,is_premium}` (`views.py:36-50`); `DELETE` anonimiza PII (ARCO) + `AuditLog DELETE_ACCOUNT_ARCO` → `204` vacío | `authentication/views.py:23-94` |
| `GET auth/metadata/` (solo `LocalJWTAuthentication` estricto) | — | `{user_id, role:user\|admin\|superuser, is_premium}` | `authentication/views.py:155-167` |

JWT: `HS256`, `aud=authenticated`, `exp=now+JWT_TTL_MINUTES(20)` (`settings.py:221-226`),
`leeway=30s` + denylist por `jti` (logout/refresh rotan `jti`; legacy sin `jti` válido hasta `exp`).
`leeway=30s` (`local_jwt_auth.py:58-65`). Claims: `sub,username,email,role,aud,exp,iat`
(`views.py:285-298`). Cliente: refrescar proactivamente (~minuto 15), 1 reintento tras `401`,
logout limpio a login. Detalle de diseño: el refresh automático se excluye en
todo `auth/*` (evita bucle 401→refresh→401); `profile/`/`consent/` con 401 van
directo a login. Rotación dispositivos IoT (`POST devices/<id>/rotate/` → `{auth_token,expires_at+90d}`,
`core/views.py:57-73`) es **flota, no APK** (dueño/staff).

## 2. Especies (catálogo público + NOM-059) — `apps/plants/`

| Método + path | Auth | Response | Código |
|---|---|---|---|
| `GET plants/search/?q=&category=` | `AllowAny` | `400 {error}` si sin filtros; `200` **array directo** (máx 50, sin envelope) `[{id,nombre,nombre_cientifico,descripcion,category,habitat,uses,humedad:"min-max%",temperatura,ph,image_url,is_endemic[,is_protected_nom059:true,protection_warning,protection_category]}]`; filtros `?q=&category=&endemic=1&habitat=` | `apps/plants/views.py:44-100` |
| `GET/POST plants/species/` + `GET/PUT/PATCH/DELETE plants/species/<pk>/` | lectura pública, escritura staff (`IsSuperuserOrReadOnly`, `apps/plants/views.py:222-237`) | lista paginada `{count,next,previous,results:[Species]}` (`PAGE_SIZE=50`, `settings.py:204-209`); `Species` 22 campos (`scientific_name,common_name,description,ideal_humidity_min/max,ideal_temp_min/max,ideal_ph_min/max/optimal,habitat,soil_type,irrigation,uses,uv_rays,soil_humidity_min/max,image_url,category,is_protected_nom059,protection_category`) | `apps/plants/serializers.py:42-71`, `views.py:232` |
| `POST plants/flora/` | `IsAuthenticated` multipart | `Flora {id,user,common_name,scientific_name,family,treatment,image}` | `apps/plants/views.py:208-219`, `serializers.py:88-92` |

**Obligación NOM-059 (LGEEPA, `enforce-compliance` Guardrail C):** si `is_protected_nom059==true`,
la UI **debe** renderizar el `protection_warning` en contenedor de advertencia
(`bg-red-500/10 border-red-500/30` en web → equivalente `ThemeData` error-container en Flutter).
Prohibido ocultar o resumir el texto legal. Cubierto por test widget obligatorio.

## 3. Mis plantas — `apps/plants/urls_user.py` (montado en `user-plants/`)

> OJO coherencia: el docstring de `my_collection_view` dice `/api/v1/plants/my-collection/`
> (`views.py:36`) pero el montaje real es **`user-plants/`** (`mole_ai_backend/urls.py:50`).
> Vale el montaje (verificado en `openapi.yml`).

| Método + path | Response |
|---|---|
| `GET user-plants/my-collection/` | **array directo** `[{id:UUID,nickname,species_id?,created_at}]` (`PlantResponseSerializer`, `serializers.py:28-32`) |
| `GET user-plants/` | envelope `{results:[…], count}` |
| `POST user-plants/` | `{nickname?,hardware_pin?,species_id?}` → `201` |
| `GET/PATCH/DELETE user-plants/<uuid>/` | scoped a `user=request.user` (`404` si ajena) |
| `GET/POST user-plants/favorites/` | `{results,count}` / `201 {id,user,plant,created_at}` |
| `DELETE user-plants/favorites/<id>/` | `204` |

Deuda corregida en Fase 1: `favorites/` ahora declarado antes de `<uuid:plant_id>/`
(`urls_user.py:22-27`) por claridad (Django ya lo resolvía: el conversor UUID
rechaza `favorites`).

## 3b. Sincronización edge con cursor (MRF03/RNF06, solo flota/daemon)

`POST sync/batch/` (`IsAuthenticated` DeviceBearer + throttle `sensor_data`,
`apps/core/views.py:SyncBatchView`, ruta `core/urls.py`): JSON-RPC 2.0 estricto,
dual-stack con `edge-batch/` (intacto).
Request: `{"jsonrpc":"2.0","method":"sync.telemetry",`
`"params":{"cursor":<iso|null>,"frames":[{ts,ri,a,s}...]},"id":any}`.
Response: `{"jsonrpc":"2.0","result":{"applied_up_to":<iso|null>,`
`"accepted":[i...],"conflicts":[{index,error,details?}...]},"id":same}`.
Errores: `-32700` parse, `-32600` request, `-32601` método, `-32602` params
(HTTP 200 con objeto error; auth 401 plano como `edge-batch/`).
Semántica: éxito parcial por trama, transacción por trama, reenvíos
idempotentes (`dedupe`), conflictos = tramas rechazadas (server-wins).
El daemon persiste el cursor en SQLite (`sync_state`) y vuelve a legacy
(`sync_to_backend`) si el backend responde 404/405/501.

## 4. Telemetría (solo lectura) — `apps/core/`

| Método + path | Response |
|---|---|
| `GET telemetry/latest/?plant_id=<uuid>` (`IsAuthenticated`, 404 si no dueño/sin logs) | `{plant_id,recorded_at:ISO,soil_humidity?,air_humidity?,air_temperature?,uv_index?,ph_level?}` (doubles o null) — `api_views.py:59-92` |
| `GET devices/<uuid>/health/` (`IsAuthenticated`) | `{device_id,device_name,status,last_seen,last_seen_delta_seconds,ambient:{…}\|null,soil:[{pin,plant_id,plant_nickname,species?,soil_humidity?,recorded_at?,ideal_*}],sre_metrics:{uptime_pct_24h,ws_reconnects_24h,report_interval_minutes}}` — `api_views.py:168-265` |
| `GET devices/<uuid>/bindings/` | `{bindings:[{id,hardware_pin,plant_id,plant_nickname,species}],count}` (`POST/DELETE` solo staff → fuera MVP) |

Nodos en deep-sleep: `last_seen_delta_seconds` + `status` gobiernan la UI ("durmiendo",
último dato `recorded_at`), nunca inventar valores.

## 5. Visión async (vía congelada) — `apps/core/` + `apps/ai_models/`

1. `POST diagnostics/` (`IsAuthenticated`, `DiagnosticsThrottle` 30/min) multipart:
   `image*` (jpeg/png/webp ≤10MB, magic-bytes `FFD8FF/89PNG/RIFF-WEBP`),
   `plant_id?`, `model_type=disease_detection|plant_identification|pest_detection|nutrient_deficiency|growth_stage`
   (`core/views.py:320-351`, `serializers.py:185-227`, `safe_join` en disco).
   → `202 {status:processing, task_id, message}`.
2. Poll `GET ai/vision/status/<task_id>/` con backoff
   → `{status:pending|success|failure, state, result?, error?, info?}`
   (`ai_models/views.py:142-160`); `result` es opaco para la vista (lo fija el
   worker Celery): cuando hay diagnóstico, `result.diagnosis` =
   `{species_common/scientific, growth_stage, affliction_name/type,
   severity:low|medium|high|critical, confidence 0-1, ph_predicted 0-14,
   immediate_actions[], disclaimer}`. Si `result` no trae `diagnosis`, la UI
   muestra `state/info` sin inventar campos.
   **Bloqueo de seguridad (Hito 4):** si el SafetyValidator detecta una especie
   protegida por NOM-059 en la respuesta de MS1, `result.blocked=true` y
   `result.safety_block={code, reason}`; la UI debe renderizar el banner rojo
   (`SafetyBlockBanner`) y no persistir el diagnóstico localmente.
3. `GET diagnostics/history/?limit=20` → `{results:[{id,plant_id,condition,analyzed_at}]}`;
   `GET diagnostics/<id>/download/` → `202 {task_id, poll_url:/api/v1/tasks/status/<id>/}`.
4. Fallo MS1 (caída NVIDIA): `status:failure + error` explícito — la UI lo muestra,
   no reintenta en bucle (sin fallback local en MVP).

## 5b. Ping y polling genérico — `apps/core/`

| Método + path | Auth | Response | Código |
|---|---|---|---|
| `GET health/` | `AllowAny` explícito (ping pre-login; solo `{status,timestamp}`, sin PII) | `{status:healthy, timestamp:ISO}` | `apps/core/views.py:health_check_view` |
| `GET tasks/status/<task_id>/` | `IsAuthenticated` | `{task_id, state:PENDING\|STARTED\|SUCCESS\|FAILURE\|RETRY, result\|error\|info}` (poll con backoff, nunca busy-loop) | `apps/core/views.py:585-624` |

## 6. Chat, mapa y reportes (implementados Fase D)

- **Chat:** `POST llm/chat/` `{question|message|prompt}` sync → `{response,sources,disclaimer}`
  (`core/views.py:521-570`, 60/min) + `GET chat/history/`; disclaimer COFEPRIS obligatorio.
  **Bloqueo de seguridad (Hito 5):** si la respuesta del LLM menciona una especie
  protegida por NOM-059 o un agroquímico catalogado, el endpoint responde `403`
  con `{error, code, source: 'chat'}`; la UI renderiza un `SafetyBlockBanner` en
  el historial y no guarda el turno en `LLMRequest`.
- **Mapa:** `GET map/hotspots/` (`IsAuthenticated`, `{hotspots:[{lat,lng,severity,species}]}`,
  `core/views.py:401-417`) + `GET weather/current/?lat&lon` (público) + tiles
  `GET weather/tile/<layer>/<z>/<x>/<y>.png` (público; `core/views.py:419-457`).
- **Reportes:** MS3 directo por el MISMO gateway (`location /api/v1/reports/` en ambos
  nginx reenvía el path completo; MS3 monta el router con prefijo `/api/v1/reports`,
  `mole_report/app/main.py:41`): `POST reports/generate` (**ruta exacta, sin `/` final**)
  `{date_range_days=90,sensors=[]}` → `{job_id,status:QUEUED}` → poll
  `GET reports/<job>/status` hasta `status==SUCCESS` (`FAILURE` → error del job) →
  `GET reports/<job>/download` → `{download_url}` presigned (~24h). JWT Bearer igual
  que el resto (ownership por `hashed_user_id`, `reports.py:27-93`). El APK abre la URL
  externamente (sin permiso de almacenamiento). Vía admin Django solo staff (fuera MVP).

## 6b. Admin app (`IsAuthenticated` + `IsAdminUser`, rol admin|superuser)

| Método + path | Request | Response | Código |
|---|---|---|---|
| `GET admin/statistics` (ruta exacta) | — | `{users:[...], regs:[...], health:[...], total_plants}` | `core/admin_views.py:admin_stats_view` |
| `GET admin/live-alerts` (ruta exacta) | — | `{alerts:[{tipo,msg,source,recorded_at,device_id,plant_id}]}` (máx 5; lee esquema vivo con fallback legacy) | `core/admin_views.py:live_alerts_view` |
| `GET admin/users/?search=&role=&page=` | query | `{count, results:[{id,username,email,role,is_active,is_premium,date_joined}]}` (50/pág) | `core/admin_views.py:admin_users_list_view` |
| `POST admin/users/create/` | `{username,password,role}` | `201`; `400` duplicado/faltantes | `core/admin_views.py:admin_users_create_view` |
| `GET/PATCH/DELETE admin/users/<id>/` | `PATCH {role,is_active}` | GET objeto; PATCH `{status,role,is_active}` (solo Superadmin otorga Superadmin o toca Superadmin); DELETE desactiva (soft) + `AuditLog` | `core/admin_views.py:admin_user_detail_view` |
| `GET training/documents/?status=` + `GET training/images/` | query | `{count, results}` (máx 100; `uploaded_by_email`, estado) | `training_data/views.py:list_*` |
| `POST training/documents/upload/request/` + `POST training/images/upload/request/` | multipart meta (ver §) | `201 {presigned_url,s3_key,record_id,expires_in:900,content_type}` | `training_data/views.py` |
| `POST training/upload/confirm/` | `{record_id, asset_type}` | `200 {record_id,status,s3_verified,file_size}`; `409` si no PENDING | `training_data/views.py:upload_confirm_view` |

## 7. Errores y throttles

| Código | Significado móvil | Acción cliente |
|---|---|---|
| `400` | request inválida (`details` en ingesta) | no reintentar; mostrar mensaje |
| `401` | JWT ausente/expirado/inválido (`aud`/`exp`) | refresh 1 vez → reintentar; si falla, logout a login |
| `403` | sin permiso (recurso ajeno, SRE-only, NOM-059 en MS directo) | no reintentar |
| `404` | planta/recurso ajeno o inexistente | tratar como "no tuyo" en `telemetry/latest/` |
| `409` | conflicto (binding duplicado, upload ya confirmado) | recargar estado |
| `429` | throttle (`anon:100/h, user:10000/min, llm_chat:60/min, diagnostics:30/min, sensor_data:200/min`, `settings.py:210-216`) | backoff exponencial + aviso |
| `501` | no implementado (`subscription PUT`, weather sin key) | no reintentar |
| `502` | fallo red contra proveedor | reintentar 1 vez |
| `202 + task_id/poll_url` | aceptado async (diagnostics, reportes, `chat/fallback`) | poll con backoff, nunca busy-loop |

## 8. Excluidos explícitamente del contrato móvil

`sensor-data/batch/` y `edge-batch/` (firmware), `POST sensors/ingest` (M2M),
stubs vacíos (`sensor-logs/`, `plant-knowledge/`, `fichas/`, `history/`, `diagnosticos/*/create/`),
mock dev `sensor-data/latest/`, `validate-token/` (Supabase legacy), `auth/debug/`,
entrenamiento (`ai/train/*`, `training/*`), admin (`admin/*`, `reports/*`),
`iot/nodes/`, `feedback/` (fase 2), `subscription/` (fase 2).

## 9. Versionado

Cambios compatibles (campos nuevos opcionales) no rompen el snapshot.
Cambios incompatibles (quitar/renombrar path o campo, cambiar envelope) exigen:
minor del contrato + entrada en issue 11 + APK y backend desplegados a la par.
El gate `schema-diff` (§11) bloquea CI ante cualquier cambio de paths/métodos no declarado.

## 10. Cumplimiento resumido (`enforce-compliance`)

- **LFPDPPP:** consentimiento registrado antes de telemetría personal; ARCO (`DELETE profile/`);
  token solo en `flutter_secure_storage`, jamás en logs ni prefs.
- **NOM-059/LGEEPA:** disclaimer §2 obligatorio + test widget.
- **IFT-016/TLS:** APK solo HTTPS (excepción: setup local); ingesta edge intacta por TLS/Store&Forward.
- **Uploads:** `safe_join` + magic-bytes ya en backend; el APK valida tamaño/tipo antes de subir.

## 11. Gate schema-diff

`scripts/check-mobile-contract.sh`: regenera el schema con las mismas env de test y
`diff` contra `docs/contracts/openapi.yml`. Integrado como job `mobile-contract`
en `.github/workflows/system-tests.yml`. Falla con diff no vacío.
