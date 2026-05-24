# SKILL: Enforce Compliance and Quality Standards (Mexican Regulations & ISO/IEC 25001)

## Meta
- **Name**: enforce-compliance
- **Description**: Evaluates, restricts, and audits any architecture plan or code modification against Mexican official standards (NOM), federal laws (LFPDPPP, LGEEPA, IFT), and the ISO/IEC 25001 Quality Requirements division.
- **Trigger**: Use when drafting execution plans, altering database schemas, modifying network/telemetry data flows, creating hardware interaction layers (ESP32), or handling file uploads/downloads.

## 1. Contexto y Marco Normativo de Referencia
Cualquier modificación al sistema Mole.AI debe alinearse obligatoriamente de forma estricta con el siguiente ecosistema regulatorio:

1. **Hardware & Telecomunicaciones (Seguridad Eléctrica)**:
   - **NOM-001-SCFI-2018**: Aparatos electrónicos - Requisitos de seguridad.
   - **NOM-019-SCFI-1998**: Seguridad de equipo de procesamiento de datos.
   - **NOM-003-SCFI-2014**: Especificaciones de seguridad en productos eléctricos.
   - **Disposición Técnica IFT-016-2024**: Dispositivos de radiocomunicación de baja potencia (RF/Wi-Fi del ESP32 en intervalos de 30 MHz a 3 GHz).
2. **Privacidad de Datos**:
   - **LFPDPPP (Ley Federal de Protección de Datos Personales en Posesión de los Particulares)**: Consentimiento explícito, cifrado en reposo/tránsito, y aislamiento de Datos Personales (PII).
3. **Biodiversidad y Medio Ambiente**:
   - **LGEEPA (Ley General del Equilibrio Ecológico y la Protección al Ambiente)** y **NOM-059-SEMARNAT**: Protección de especies endémicas. La UI debe inyectar *disclaimers* y advertencias explícitas sobre penalizaciones de extracción ilegal al consultar o procesar estas especies en el catálogo de flora.
4. **Calidad de Software**:
   - **ISO/IEC 25001 (SQUARE - Quality Requirements)**: Definición, especificación, gestión y control de requisitos de calidad del producto de software a través de ciclos de vida rigurosos.

---

## 2. Fases de Ejecución Obligatorias (Workflow)

El agente tiene estrictamente prohibido modificar archivos o proponer código sin pasar por las siguientes 4 fases secuenciales:

### Fase 1: Explore & Scope (Lectura de Impacto)
Antes de proponer una solución, mapea qué capas del sistema se verán afectadas y asócialas a sus regulaciones pertinentes:
- Si el cambio toca el **ESP32 o el Gateway de Telemetría (OpenClaw)** ──> Validar impacto en *NOM-001/019/003* e *IFT-016-2024* (cifrado TLS de datos de radiofrecuencia).
- Si el cambio altera el **Registro, Base de Datos o Autenticación** ──> Validar cumplimiento de la *LFPDPPP* (Ciclo de vida del dato, protección de contraseñas, tokens de sesión).
- Si el cambio modifica la **Visualización de Especies, Plantas o la Wiki** ──> Validar inyección automática de avisos de protección conforme a *LGEEPA/NOM-059*.

### Fase 2: Present Compliance Candidates (Análisis de Riesgo)
Presenta al operador un desglose numerado de los impactos regulatorios detectados en la Fase 1 bajo el estándar **ISO/IEC 25001**, evaluando:
1. **Adecuación Funcional**: ¿El cambio altera las reglas de negocio legítimas?
2. **Eficiencia de Rendimiento**: ¿La validación extra degrada los tiempos de respuesta del API?
3. **Seguridad e Integridad**: ¿Previene activamente vulnerabilidades como Path Traversal, inyecciones SQL o fugas de tokens?

### Fase 3: The Grilling & Compliance Loop
Entabla una sesión de preguntas y respuestas cortas con el operador (HITL) para resolver ambigüedades sobre el almacenamiento de datos o restricciones de hardware. Modifica el plan según las respuestas obtenidas.

### Fase 4: Codificación Segura e Inspección Post-Mortem
Aplica los cambios directamente en el entorno de producción (EC2) o el repositorio utilizando abstracciones profundas (*Deep Modules*). Al terminar, limpia todos los logs de depuración internos y añade documentación clara (ADRs) de por qué se tomó esa decisión de diseño con base en la norma correspondiente.

---

## 3. Directivas Inquebrantables de Código (Guardrails)

### Guardrail A: Privacidad e IoT (LFPDPPP + IFT-016)
- **Cero Texto Plano**: Está estrictamente prohibido transmitir telemetría del microcontrolador sin cifrado. Si falla el handshake TLS, el Gateway debe entrar en un estado seguro (*Fail-Safe Mode*) y registrar la anomalía en el SQLite local de contingencia (*Store & Forward*), notificando inmediatamente al backend.
- **Tokens y Sesiones**: El cliente frontend siempre debe exigir e inyectar el token `X-CSRFToken` y configurar `credentials: "include"` para evitar ataques transfronterizos (CSRF).

### Guardrail B: Protección de Recursos e Ingesta de Archivos (NOM-019 + SQUARE)
- **Construcción Segura de Rutas**: Queda estrictamente prohibido usar concatenaciones crudas (`os.path.join`, f-strings) con nombres de archivos proporcionados por el usuario para almacenar imágenes de diagnósticos o PDFs de la Wiki. Debe usarse siempre `django.utils._os.safe_join` o normalizadores que impidan ataques de *Path Traversal*.
- **Validación Robusta de Parámetros**: Toda función interna o router de FastAPI/Django que invoque recursos críticos (como almacenes de vectores `PGVector` o inferencia de modelos CNN) debe validar explícitamente la presencia de la firma completa de argumentos requeridos, evitando el lanzamiento de excepciones genéricas `TypeError` en producción.

### Guardrail C: Responsabilidad Ambiental (LGEEPA + NOM-059)
- **Disclaimers Mandatorios**: Si una consulta de la base de datos de especies o un diagnóstico de IA arroja una planta catalogada bajo estatus de protección especial por la NOM-059, la interfaz del frontend debe renderizar de manera mandatoria un contenedor visual de advertencia (`bg-red-500/10 border-red-500/30`) que detalle de forma explícita que la extracción ilegal del espécimen está penada por las leyes federales de México.

---

## 4. Criterios de Aceptación de la Skill
Un plan o código se considera exitoso si y solo si:
1. Pasa el analizador estático local (`pnpm run build` / linters de Python) sin arrojar advertencias de variables implícitas o imports rotos.
2. Cumple con la prueba de borrado de complejidad de la ISO 25001: Si eliminas el wrapper o adaptador de cumplimiento introducido, la seguridad del sistema debe colapsar; si la complejidad se dispersa en múltiples archivos de forma innecesaria, el módulo está mal diseñado y debe volver a la Fase 4.
3. El escaneo de SonarQube reporta **0 Blocker Vulnerabilities** relacionadas con los archivos modificados.