# Issue 16: Ampliar backend-quality/pytest + e2e con Django

Status: ready-for-agent
Sev: P2 · Área: CI · Fase: D

## Evidencia
- `system-tests.yml:54-77` ruff exactamente 7 ficheros (comentario admite deuda,
  issue 12); pytest `:79-94` exactamente 5 ficheros.
- `docker-compose.e2e.yml:1-2` `django-backend excluded due to pre-existing import bug`.

## Problema
MayorÍa de endpoints sin gate; verde falso en CI.

## Aceptación
- Resolver el import bug y re-incluir django en e2e; ampliar ruff+pytest por
  paquetes (meta: todo `apps/`), cerrando issue 12 o absorbiéndolo aquí.
- CI en verde con el alcance ampliado.

## Compliance
Calidad ISO/IEC 25001: cobertura de gates acorde al riesgo.

## Comments
(none)
