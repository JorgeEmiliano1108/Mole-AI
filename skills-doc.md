# DOCUMENTACIÓN DE ARCHIVOS — SKILLS-MAIN
## Catálogo Detallado de Skills para Agentes de IA (Matt Pocock)

---

## 1. ESTRUCTURA RAÍZ

### `/skills-main/README.md`
**Propósito**: Es la **página principal de documentación** del repositorio de skills. Contiene:
- Descripción general de las skills como herramientas para "ingenieros reales, no vibe coding"
- Guía de inicio rápido (30 segundos) para instalar skills vía `npx skills@latest`
- Explicación de los 4 problemas que resuelven: alineación agente-usuario, verbosidad excesiva, código que no funciona, y código desorganizado (ball of mud)
- Listado completo de skills por categoría (Engineering, Productivity, Misc) con enlaces a sus respectivos `SKILL.md`
- Referencias a libros fundamentales: *The Pragmatic Programmer*, *Domain-Driven Design*, *Extreme Programming Explained*, *A Philosophy of Software Design*

### `/skills-main/CLAUDE.md`
**Propósito**: Archivo de configuración que define la **estructura organizacional de las skills** para el agente Claude. Contiene:
- Reglas de organización: `engineering/`, `productivity/`, `misc/`, `personal/`, `deprecated/`
- Reglas de visibilidad: Las skills en `personal/` y `deprecated/` NO deben aparecer en `README.md` ni en `plugin.json`
- Requisitos de documentación: Cada skill debe tener referencia en README.md y entrada en `.claude-plugin/plugin.json`
- Formato de listados: Cada bucket folder tiene su propio `README.md` con descripciones de una línea

### `/skills-main/CONTEXT.md`
**Propósito**: Define el **glosario de términos del dominio** (Domain Language) para las skills de Matt Pocock. Contiene:
- Definición de "Issue tracker": La herramienta que aloja issues (GitHub Issues, Linear, `.scratch/`)
- Definición de "Issue": Una unidad de trabajo trackeada (bug, tarea, PRD, slice)
- Definición de "Triage role": Etiquetas de máquina de estado aplicadas durante triage (`needs-triage`, `ready-for-agent`, etc.)
- Relaciones: Un Issue tracker contiene muchos Issues; un Issue lleva un Triage role a la vez
- Ambigüedades resueltas: "backlog" ya no se usa; se reemplazó por "Issue tracker"

### `/skills-main/LICENSE`
**Propósito**: Archivo de licencia del repositorio (típicamente MIT, Apache 2.0 o similar). Define los términos legales de uso, modificación y distribución de las skills.

### `/skills-main/.claude-plugin/plugin.json`
**Propósito**: Archivo de configuración JSON para que **Claude Code reconozca y cargue las skills**. Contiene:
- Nombre del plugin: `"mattpocock-skills"`
- Array `"skills"`: Lista de rutas relativas a cada skill activa (9 skills en total)
- Skills incluidas: `diagnose`, `grill-with-docs`, `triage`, `improve-codebase-architecture`, `setup-matt-pocock-skills`, `tdd`, `to-issues`, `to-prd`, `zoom-out`, `caveman`, `grill-me`, `write-a-skill`

### `/skills-main/scripts/link-skills.sh`
**Propósito**: Script de utilidad para **instalar o enlazar las skills** en un proyecto. Probablemente contiene lógica para:
- Crear enlaces simbólicos o copiar archivos de skills al directorio `.claude/` del proyecto
- Configurar el archivo `CLAUDE.md` o `AGENTS.md` para referenciar las skills
- Automatizar la ejecución de `/setup-matt-pocock-skills`

---

## 2. DIRECTORIO `.out-of-scope/`

### `/skills-main/.out-of-scope/mainstream-issue-trackers-only.md`
**Propósito**: Define qué **NO está dentro del alcance** de las skills de triage. Contiene:
- Regla: Solo se debe hacer triage de issues en trackers principales (GitHub Issues, GitLab Issues, Linear)
- No hacer triage de tickets en Jira, Trello, Monday.com u otros sistemas no soportados
- Criterios para determinar cuándo cerrar un issue como `wontfix` por estar fuera de alcance

### `/skills-main/.out-of-scope/question-limits.md`
**Propósito**: Establece **límites y restricciones** para las preguntas durante sesiones de grilling. Contiene:
- Cuándo dejar de hacer preguntas y tomar una decisión
- Cómo evitar parálisis por análisis durante el triage
- Cuándo escalar a un humano en lugar de seguir preguntando

---

## 3. DIRECTORIO `docs/adr/`

### `/skills-main/docs/adr/0001-explicit-setup-pointer-only-for-hard-dependencies.md`
**Propósito**: **Architectural Decision Record (ADR)** que documenta una decisión de diseño importante. Contiene:
- Decisión: El comando `/setup-matt-pocock-skills` debe ejecutarse explícitamente antes de usar otras skills
- Contexto: Las skills tienen dependencias "duras" (issue tracker, triage labels, domain docs) que deben configurarse por proyecto
- Alternativas consideradas: Autodetección vs configuración manual
- Consecuencia: Las skills fallarán con error descriptivo si no se ejecuta setup primero

---

## 4. SKILLS DE ENGINEERING (TRABAJO DIARIO DE CÓDIGO)

### `/skills-main/skills/engineering/README.md`
**Propósito**: Lista todas las skills en la categoría `engineering/` con descripciones de una línea. Actúa como índice dentro del bucket.

### `/skills-main/skills/engineering/diagnose/SKILL.md`
**Propósito**: Skill de **diagnóstico disciplinado para bugs difíciles y regresiones de rendimiento**. Implementa un proceso de 6 fases:
1. **Build a feedback loop** (Lo más crítico): Crear un bucle reproducible y determinista (test fallante, script curl, headless browser, replay de trace, etc.)
2. **Reproduce**: Ejecutar el bucle y confirmar que el fallo coincide con lo reportado por el usuario
3. **Hypothesise**: Generar 3-5 hipótesis falsificables antes de probarlas
4. **Instrument**: Agregar logs/debuggers dirigidos, cambiando una variable a la vez
5. **Fix + regression test**: Escribir test ANTES del fix; aplicar fix; verificar que el test pase
6. **Cleanup + post-mortem**: Eliminar logs `[DEBUG-...]`, borrar prototipos, documentar la causa raíz

**Cuándo usar**: "diagnose this", "debug this", reporta un bug, algo está fallando, regresión de rendimiento.

### `/skills-main/skills/engineering/diagnose/scripts/hitl-loop.template.sh`
**Propósito**: Template de script **Human-in-the-Loop (HITL)** para bugs que requieren interacción humana. Contiene:
- Funciones `step` (muestra instrucción, espera Enter) y `capture` (hace pregunta, lee respuesta)
- Estructura para editar: definir pasos de reproducción y capturar variables (ERROR_OCCURRED, ERROR_MSG)
- Salida al final: imprime `KEY=VALUE` para que el agente parseé los resultados

### `/skills-main/skills/engineering/grill-with-docs/SKILL.md`
**Propósito**: Skill de **grilling session** que desafía planes contra el modelo de dominio existente, afina terminología y actualiza documentación (`CONTEXT.md`, ADRs) en línea. Diferencias clave vs `grill-me`:
- **Sí** actualiza documentación (CONTEXT.md, ADRs) durante la sesión
- Usa formatos específicos: `CONTEXT-FORMAT.md` y `ADR-FORMAT.md`
- Ofrece crear ADRs solo cuando se cumplen 3 criterios: difícil de revertir, sorprendente sin contexto, resultado de un trade-off real

**Cuándo usar**: Stress-test de un plan, alinear terminología con el proyecto, documentar decisiones arquitectónicas.

### `/skills-main/skills/engineering/grill-with-docs/CONTEXT-FORMAT.md`
**Propósito**: Template que define el **formato exacto** para escribir/actualizar `CONTEXT.md`. Especifica:
- Cómo definir términos de dominio (glosario)
- Qué incluir (términos significativos para expertos del dominio, NO detalles de implementación)
- Formato de relaciones entre conceptos

### `/skills-main/skills/engineering/grill-with-docs/ADR-FORMAT.md`
**Propósito**: Template que define el **formato exacto** para escribir Architectural Decision Records (ADRs). Especifica:
- Estructura: Title, Context, Decision, Consequences
- Cuándo escribir uno (solo para decisiones difíciles de revertir, sorprendentes, con trade-offs reales)
- Dónde guardarlos: `docs/adr/` en la raíz o contexto específico

### `/skills-main/skills/engineering/improve-codebase-architecture/SKILL.md`
**Propósito**: Skill para **encontrar oportunidades de deepening** (refactoring hacia módulos profundos) en una codebase. Basada en *A Philosophy of Software Design*. Contiene:
- Glosario de términos arquitectónicos: Module, Interface, Implementation, Depth, Seam, Adapter, Leverage, Locality
- Proceso de 3 pasos:
  1. **Explore**: Leer `CONTEXT.md` y ADRs; usar Agent tool para caminar la codebase
  2. **Present candidates**: Lista numerada de oportunidades con archivos, problema, solución, beneficios
  3. **Grilling loop**: Una vez elegido un candidato, sesión de grilling para definir el diseño del módulo profundo
- Usa la **deletion test**: Imaginar que borras el módulo; si la complejidad desaparece, era inútil; si reaparece en N callers, valía la pena

**Cuándo usar**: Mejorar arquitectura, encontrar oportunidades de refactoring, consolidar módulos acoplados, hacer codebase más testeable.

### `/skills-main/skills/engineering/improve-codebase-architecture/LANGUAGE.md`
**Propósito**: Define el **glosario de términos arquitectónicos** usados en la skill `improve-codebase-architecture`. Contiene definiciones exactas de:
- Module, Interface, Implementation, Depth, Seam, Adapter, Leverage, Locality
- Principios clave: "The interface is the test surface", "One adapter = hypothetical seam"

### `/skills-main/skills/engineering/improve-codebase-architecture/DEEPENING.md`
**Propósito**: Guía detallada sobre **cómo convertir módulos shallow en deep modules**. Explica:
- Diferencia entre shallow (interfaz casi tan compleja como implementación) vs deep (mucho comportamiento detrás de una interfaz pequeña)
- Técnicas de deepening: ocultar complejidad, simplificar interfaces, mover lógica al interior
- Ejemplos antes/después de módulos deepened

### `/skills-main/skills/engineering/improve-codebase-architecture/INTERFACE-DESIGN.md`
**Propósito**: Guía para **diseñar interfaces efectivas** para módulos profundos. Contiene:
- Qué debe incluir una interfaz (tipos, invariantes, modos de error, orden, configuración)
- Cómo no acoplarse a detalles de implementación
- Cómo diseñar para testability

### `/skills-main/skills/engineering/tdd/SKILL.md`
**Propósito**: Skill de **Test-Driven Development (TDD)** con ciclo red-green-refactor. Implementa "vertical slices" (tracer bullets), NO "horizontal slices". Contiene:
- **Filosofía**: Tests deben verificar comportamiento a través de interfaces públicas, NO detalles de implementación
- **Anti-patrón**: No escribir todos los tests primero (horizontal), sino un test → implementación → siguiente test (vertical)
- **Workflow**:
  1. Planning: Confirmar interfaz, comportamientos a testear, oportunidades de deep modules
  2. Tracer Bullet: Un test → falla → código mínimo → pasa
  3. Incremental Loop: Para cada comportamiento restante: RED→GREEN
  4. Refactor: Extraer duplicación, deepen modules, aplicar SOLID (solo después de GREEN)
- **Checklist**: Test describe comportamiento, usa interfaz pública, sobreviviría a un refactor

**Cuándo usar**: "red-green-refactor", desarrollo guiado por tests, integration tests, "test-first development".

### `/skills-main/skills/engineering/tdd/tests.md`
**Propósito**: Ejemplos de **buenos y malos tests** para TDD. Contiene:
- Ejemplos de tests "buenos" (integration-style, ejercen APIs públicas, leen como especificaciones)
- Ejemplos de tests "malos" (acoplados a implementación, mockean colaboradores internos, verifican BD directamente)
- Cómo sobrevivir refactors: Si renombras una función interna y el test falla, ese test estaba mal diseñado

### `/skills-main/skills/engineering/tdd/mocking.md`
**Propósito**: Guía de **cómo y cuándo usar mocks** en TDD. Contiene:
- Cuándo mockear (dependencias externas lentas/costosas) y cuándo NO (lógica interna)
- Alternativas a mocks: usar implementaciones reales, test doubles, fakes
- Errores comunes: mockitis (mockear demasiado), tests frágiles

### `/skills-main/skills/engineering/tdd/interface-design.md`
**Propósito**: Guía específica para **diseñar interfaces testeables** antes de escribir tests. Contiene:
- Cómo diseñar interfaces que exponen comportamiento, no datos
- Cómo hacer que el módulo sea testeable a través de su interfaz pública
- Relación entre interface design y TDD

### `/skills-main/skills/engineering/tdd/deep-modules.md`
**Propósito**: Guía sobre **módulos profundos en el contexto de TDD**. Explica:
- Cómo TDD revela oportunidades para deepening
- Cómo escribir tests que ejercen toda la profundidad del módulo
- Relación entre "small interface, deep implementation" y testability

### `/skills-main/skills/engineering/tdd/refactoring.md`
**Propósito**: Guía de **refactoring seguro** durante la fase REFACTOR de TDD. Contiene:
- Regla de oro: NUNCA refactorizar mientras estés en ROJO (RED); llegar a VERDE primero
- Qué refactorizar: duplicación, módulos shallow, principios SOLID
- Cómo ejecutar tests después de cada paso de refactoring

### `/skills-main/skills/engineering/to-issues/SKILL.md`
**Propósito**: Skill para **romper un plan, especificación o PRD en issues independientes** usando vertical slices (tracer bullets). Contiene:
- Proceso de 5 pasos: Gather context → Explore codebase → Draft vertical slices → Quiz user → Publish issues
- **Reglas de vertical slices**: Cada issue corta a través de TODAS las capas (schema, API, UI, tests); es completo y demoable
- Tipos: HITL (requiere intervención humana) vs AFK (puede implementarse sin humano)
- Template de issue body con: Parent, What to build, Acceptance criteria, Blocked by
- Publica issues en orden de dependencias, aplicando la etiqueta `needs-triage`

**Cuándo usar**: Convertir un plan en issues, crear tickets de implementación, romper trabajo en issues.

### `/skills-main/skills/engineering/to-prd/SKILL.md`
**Propósito**: Skill para **transformar el contexto actual de la conversación en un PRD** (Product Requirements Document) y publicarlo en el issue tracker. Contiene:
- **No entrevista al usuario**: Solo sintetiza lo que ya se discutió
- Proceso de 3 pasos: Explore repo → Sketch modules → Write PRD
- Template de PRD con secciones: Problem Statement, Solution, User Stories (formato: "As a <actor>, I want <feature>, so that <benefit>"), Implementation Decisions, Testing Decisions, Out of Scope, Further Notes
- Enfatiza: NO incluir rutas de archivos o fragmentos de código en Implementation Decisions (se desactualizan rápido)

**Cuándo usar**: "Create a PRD", "turn this into a PRD", "write a product requirements document".

### `/skills-main/skills/engineering/triage/SKILL.md`
**Propósito**: Skill para **triage de issues** a través de una máquina de estados con roles específicos. Contiene:
- **Roles de categoría**: `bug` (algo está roto), `enhancement` (nueva función)
- **Roles de estado**: `needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`
- Proceso: Query issue tracker → Mostrar 3 buckets (Unlabeled, needs-triage, needs-info con actividad) → Triage issue específico (Gather context → Recommend → Reproduce → Grill → Apply outcome)
- Templates: Agent brief (`AGENT-BRIEF.md`), Needs-info template
- Cada comentario durante triage debe empezar con: `> *This was generated by AI during triage.*`

**Cuándo usar**: "triage issues", "review incoming bugs", "prepare issues for AFK agent", "manage issue workflow".

### `/skills-main/skills/engineering/triage/AGENT-BRIEF.md`
**Propósito**: Template para escribir **briefs de agente** cuando un issue llega a `ready-for-agent`. Contiene:
- Formato estructurado: Context, Steps to reproduce, Expected behavior, Acceptance criteria
- Lo suficientemente detallado para que un agente AFK pueda implementar sin intervención humana
- Diferencia con `ready-for-human`: este último requiere juicio humano, testing manual, o decisiones de diseño

### `/skills-main/skills/engineering/triage/OUT-OF-SCOPE.md`
**Propósito**: Define cómo manejar **issues fuera de alcance** durante triage. Contiene:
- Criterios para determinar si un issue está fuera de alcance
- Proceso para escribir a `.out-of-scope/*.md` y cerrar el issue con `wontfix`
- Formato para documentar el rechazo (para evitar re-sugerencias en futuras auditorías)

### `/skills-main/skills/engineering/setup-matt-pocock-skills/SKILL.md`
**Propósito**: Skill **fundamental** que configura `AGENTS.md`/`CLAUDE.md` y `docs/agents/` para que las demás skills sepan:
- **Issue tracker**: Dónde viven los issues (GitHub, GitLab, Local markdown `.scratch/`)
- **Triage labels**: Strings usados para los 5 roles canónicos de triage
- **Domain docs**: Dónde viven `CONTEXT.md` y ADRs (single-context vs multi-context)

Proceso de 5 pasos: Explore → Present findings → Confirm → Edit `AGENTS.md`/`CLAUDE.md` → Write `docs/agents/*.md`

**Cuándo usar**: ANTES de usar `to-issues`, `to-prd`, `triage`, `diagnose`, `tdd`, `improve-codebase-architecture`, o `zoom-out`.

### `/skills-main/skills/engineering/setup-matt-pocock-skills/issue-tracker-github.md`
**Propósito**: Template para configurar un **issue tracker de GitHub**. Contiene:
- Cómo usar el CLI `gh` para crear issues
- Formato de descripción: "GitHub — issues live in the repo's GitHub Issues (uses the `gh` CLI)"
- Mapeo de triage roles a etiquetas reales de GitHub

### `/skills-main/skills/engineering/setup-matt-pocock-skills/issue-tracker-gitlab.md`
**Propósito**: Template para configurar un **issue tracker de GitLab**. Contiene:
- Cómo usar el CLI `glab` para crear issues
- Formato de descripción: "GitLab — issues live in the repo's GitLab Issues (uses the `glab` CLI)"
- Mapeo de triage roles a etiquetas reales de GitLab

### `/skills-main/skills/engineering/setup-matt-pocock-skills/issue-tracker-local.md`
**Propósito**: Template para configurar un **issue tracker local (markdown)**. Contiene:
- Dónde guardar issues: `.scratch/<feature>/` en el repositorio
- Formato de archivos markdown para issues locales
- Bueno para proyectos solitarios o repos sin remoto

### `/skills-main/skills/engineering/setup-matt-pocock-skills/triage-labels.md`
**Propósito**: Template para mapear **roles de triage a etiquetas reales**. Contiene:
- Formato: `needs-triage` → etiqueta real, `ready-for-agent` → etiqueta real, etc.
- Cómo manejar cuando el repositorio usa nombres diferentes (ej. `bug:triage` en lugar de `needs-triage`)

### `/skills-main/skills/engineering/setup-matt-pocock-skills/domain.md`
**Propósito**: Template para definir **reglas de consumo de domain docs**. Contiene:
- Cómo leer `CONTEXT.md` y `CONTEXT-MAP.md`
- Reglas para single-context vs multi-context
- Dónde buscar ADRs (raíz o por contexto específico)

### `/skills-main/skills/engineering/zoom-out/SKILL.md`
**Propósito**: Skill que le dice al agente que **haga zoom out y dé contexto más amplio** o una perspectiva de mayor nivel. Contiene:
- Instrucción simple: "I don't know this area of code well. Go up a layer of abstraction. Give me a map of all the relevant modules and callers, using the project's domain glossary vocabulary."
- **Desactiva invocación de modelo** (`disable-model-invocation: true`)

**Cuándo usar**: No conoces bien una sección de código, necesitas entender cómo encaja en el panorama general.

---

## 5. SKILLS DE PRODUCTIVITY (HERRAMIENTAS DE FLUJO DE TRABAJO NO-CÓDIGO)

### `/skills-main/skills/productivity/README.md`
**Propósito**: Lista todas las skills en la categoría `productivity/` con descripciones de una línea.

### `/skills-main/skills/productivity/caveman/SKILL.md`
**Propósito**: Skill de **comunicación ultra-comprimida** que reduce el uso de tokens ~75%. Contiene:
- Reglas: Eliminar artículos (a/an/the), filler (just/really/basically), cortesías (sure/certainly), conjunciones
- Usar fragmentos, abreviaciones (DB/auth/config/req/res/fn/impl), flechas para causalidad (X -> Y)
- **Persistencia**: Se activa con "caveman mode", "talk like caveman", "be brief"; permanece activa hasta "stop caveman" o "normal mode"
- **Excepción Auto-Clarity**: Desactiva temporalmente para advertencias de seguridad, acciones irreversibles, secuencias de pasos múltiples

**Cuándo usar**: "caveman mode", "less tokens", "be brief", "use caveman".

### `/skills-main/skills/productivity/grill-me/SKILL.md`
**Propósito**: Skill de **grilling session** que entrevista al usuario implacablemente sobre un plan hasta alcanzar entendimiento compartido. Similar a `grill-with-docs` PERO:
- **NO** actualiza documentación (no toca CONTEXT.md ni ADRs)
- Hace preguntas de una en una, esperando feedback
- Si una pregunta puede responderse explorando la codebase, la explora en lugar de preguntar

**Cuándo usar**: "grill me", "stress-test my plan", "interview me about this design".

### `/skills-main/skills/productivity/write-a-skill/SKILL.md`
**Propósito**: Skill para **crear nuevas skills** con estructura adecuada, progressive disclosure y recursos empaquetados. Contiene:
- Proceso de 3 pasos: Gather requirements → Draft skill → Review with user
- **Estructura de skill**:
  ```
  skill-name/
  ├── SKILL.md           # Instrucciones concisas (requerido)
  ├── REFERENCE.md      # Docs detalladas (si >500 líneas)
  ├── EXAMPLES.md       # Ejemplos de uso
  └── scripts/          # Scripts utilitarios
  ```
- **Requisitos de descripción**: Máximo 1024 chars, tercera persona, formato: "What it does. Use when [triggers]"
- Cuándo agregar scripts: operaciones deterministas, mismo código generado repetidamente, manejo explícito de errores

**Cuándo usar**: "create a skill", "write a new skill", "build a skill".

---

## 6. SKILLS MISC (HERRAMIENTAS MENOS USADAS)

### `/skills-main/skills/misc/README.md`
**Propósito**: Lista todas las skills en la categoría `misc/` con descripciones de una línea.

### `/skills-main/skills/misc/git-guardrails-claude-code/SKILL.md`
**Propósito**: Skill para **configurar hooks en Claude Code** que bloquean comandos git peligrosos antes de ejecutarlos. Contiene:
- **Comandos bloqueados**: `git push`, `git reset --hard`, `git clean -f`, `git branch -D`, `git checkout .`, `git restore .`
- Proceso: Ask scope (project vs global) → Copy script → Add hook to settings.json → Customize → Verify
- Usa `.claude/settings.json` (proyecto) o `~/.claude/settings.json` (global)

**Cuándo usar**: "prevent dangerous git operations", "add git safety hooks", "block git push in Claude Code".

### `/skills-main/skills/misc/git-guardrails-claude-code/scripts/block-dangerous-git.sh`
**Propósito**: Script bash que **intercepta y bloquea comandos git peligrosos**. Contiene:
- Lógica para parsear el JSON pasado por el hook PreToolUse de Claude Code
- Detecta patrones peligrosos y sale con código 2 (bloqueado)
- Mensaje de error: "You do not have authority to access these commands"

### `/skills-main/skills/misc/migrate-to-shoehorn/SKILL.md`
**Propósito**: Skill para **migrar archivos de test de `as` type assertions a @total-typescript/shoehorn** en TypeScript. Contiene:
- Por qué usar shoehorn: permite pasar datos parciales mientras TypeScript se mantiene feliz
- Patrones de migración: `as Type` → `fromPartial()`, `as unknown as Type` → `fromAny()`
- Cuándo usar cada función: `fromPartial()` (datos parciales), `fromAny()` (datos intencionalmente incorrectos), `fromExact()` (objeto completo)
- Workflow: Install → Find `as` assertions → Replace → Add imports → Run type check

**Cuándo usar**: "migrate to shoehorn", "replace as in tests", "need partial test data".

### `/skills-main/skills/misc/scaffold-exercises/SKILL.md`
**Propósito**: Skill para **crear estructuras de directorios de ejercicios** con secciones, problemas, soluciones y explainers que pasen linting. Contiene:
- **Convenciones de nombres**: `XX-section-name/` (secciones), `XX.YY-exercise-name/` (ejercicios), dash-case
- **Variantes de ejercicio**: `problem/` (espacio del estudiante), `solution/` (implementación de referencia), `explainer/` (material conceptual)
- **Archivos requeridos**: `readme.md` no vacío en cada subfolder, `main.ts` si hay código
- **Workflow**: Parse plan → Create directories → Create stub readmes → Run lint (`pnpm ai-hero-cli internal lint`) → Fix errors
- Reglas de linting: no `.gitkeep`, no `speaker-notes.md`, no broken links

**Cuándo usar**: "scaffold exercises", "create exercise stubs", "set up a new course section".

### `/skills-main/skills/misc/setup-pre-commit/SKILL.md`
**Propósito**: Skill para **configurar Husky pre-commit hooks** con lint-staged (Prettier), type checking y tests. Contiene:
- **Qué configura**: Husky pre-commit hook, lint-staged ejecutando Prettier, config de Prettier (si falta), scripts typecheck y test en el hook
- Proceso de 8 pasos: Detect package manager → Install deps → Init Husky → Create `.husky/pre-commit` → Create `.lintstagedrc` → Create `.prettierrc` → Verify → Commit
- **Compatibilidad**: npm, pnpm, yarn, bun

**Cuándo usar**: "add pre-commit hooks", "set up Husky", "configure lint-staged".

---

## 7. SKILLS PERSONAL (VINCULADAS A LA CONFIGURACIÓN DEL AUTOR)

### `/skills-main/skills/personal/README.md`
**Propósito**: Lista todas las skills en la categoría `personal/` con descripciones de una línea. Nota: Estas skills están **vinculadas al setup del autor (Matt Pocock)** y NO se promocionan para uso general.

### `/skills-main/skills/personal/edit-article/SKILL.md`
**Propósito**: Skill para **editar y mejorar artículos** reestructurando secciones, mejorando claridad y apretando prosa. Contiene:
- Proceso de 2 pasos:
  1. Dividir artículo en secciones basado en headings; confirmar secciones con usuario
  2. Para cada sección: reescribir para mejorar claridad, coherencia y flujo; máximo 240 caracteres por párrafo

**Cuándo usar**: "edit this article", "revise my article", "improve this draft".

### `/skills-main/skills/personal/obsidian-vault/SKILL.md`
**Propósito**: Skill para **buscar, crear y gestionar notas** en el Obsidian vault del autor. Contiene:
- **Ubicación del vault**: `/mnt/d/Obsidian Vault/AI Research/` (específico del autor)
- **Convenciones de nombres**: Title Case, sin carpetas, usar `[[wikilinks]]`
- **Index notes**: Agregan temas relacionados (ej. `RAG Index.md`)
- **Workflows**: Search (find/grep), Create new note, Find related notes (backlinks), Find index notes

**Cuándo usar**: "find a note in Obsidian", "create a new note", "organize my Obsidian vault".

---

## 8. SKILLS DEPRECATED (YA NO SE USAN)

### `/skills-main/skills/deprecated/README.md`
**Propósito**: Lista las skills en `deprecated/` indicando que **ya no se usan**. Estas skills NO deben aparecer en `README.md` ni en `plugin.json`.

### `/skills-main/skills/deprecated/design-an-interface/SKILL.md`
**Propósito**: Skill **deprecada** que generaba **múltiples diseños radicalmente diferentes de interfaces** usando sub-agentes paralelos. Basada en "Design It Twice" de *A Philosophy of Software Design*. Contenía:
- Proceso de 5 pasos: Gather Requirements → Generate Designs (3+ sub-agents paralelos) → Present Designs → Compare Designs → Synthesize
- Criterios de evaluación: Interface simplicity, General-purpose vs specialized, Implementation efficiency, Depth
- Anti-patrones: No dejar que sub-agentes produzcan diseños similares, no omitir comparación

**Cuándo se usaba**: "design an API", "explore interface options", "compare module shapes", "design it twice".

### `/skills-main/skills/deprecated/qa/SKILL.md`
**Propósito**: Skill **deprecada** de QA (Quality Assurance). Probablemente contenía procesos para revisión de calidad de código, pero fue reemplazada por otras skills más específicas.

### `/skills-main/skills/deprecated/request-refactor-plan/SKILL.md`
**Propósito**: Skill **deprecada** para solicitar planes de refactoring. Probablemente evolucionó hacia `improve-codebase-architecture`.

### `/skills-main/skills/deprecated/ubiquitous-language/SKILL.md`
**Propósito**: Skill **deprecada** para establecer lenguaje ubicuo (Domain-Driven Design). Su funcionalidad fue absorbida por `setup-matt-pocock-skills` y `grill-with-docs`.

---

## APÉNDICE: MAPA DE NAVEGACIÓN RÁPIDA

| Si necesitas... | Usa este archivo SKILL.md |
|----------------|---------------------------|
| Diagnosticar bugs difíciles | `engineering/diagnose/` |
| Stress-test un plan y documentar | `engineering/grill-with-docs/` |
| Mejorar arquitectura | `engineering/improve-codebase-architecture/` |
| Hacer TDD (red-green-refactor) | `engineering/tdd/` |
| Entender código ajeno (zoom out) | `engineering/zoom-out/` |
| Configurar repo para skills | `engineering/setup-matt-pocock-skills/` |
| Convertir plan a issues | `engineering/to-issues/` |
| Crear un PRD | `engineering/to-prd/` |
| Triage de issues | `engineering/triage/` |
| Comunicación breve (75% menos tokens) | `productivity/caveman/` |
| Grilling session simple | `productivity/grill-me/` |
| Crear una nueva skill | `productivity/write-a-skill/` |
| Bloquear git push/reset en Claude | `misc/git-guardrails-claude-code/` |
| Migrar tests a shoehorn | `misc/migrate-to-shoehorn/` |
| Crear ejercicios de curso | `misc/scaffold-exercises/` |
| Configurar pre-commit hooks | `misc/setup-pre-commit/` |
| Editar un artículo | `personal/edit-article/` |
| Gestionar Obsidian vault | `personal/obsidian-vault/` |

---

*Documento generado automáticamente basado en el análisis de la estructura de `skills-main/` de Matt Pocock.*
