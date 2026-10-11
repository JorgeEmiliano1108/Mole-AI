# 16: RNF-MS-01: Desacoplamiento ante falla de Web Mining

Status: ready-for-human

## Requisito

- **ID:** RNF-MS-01
- **Capa:** Microservicios y Web Mining
- **Tipo:** RNF
- **Texto:** La arquitectura debe mantener un bajo acoplamiento. Si el microservicio de Web Mining falla o está en mantenimiento, el Backend de Django debe seguir operando las consultas transaccionales de los usuarios sin interrupción.

## Veredicto

⚠️ PARCIAL — Patrones de desacoplamiento probados para MS1/MS2/MS3; Web Mining no existe para verificar escenario específico.

## Evidencia

- Fallback AI: `core_backend/apps/core/infrastructure/clients/microservices.py:287-333`.
- Retries con tenacity: `core_backend/apps/core/infrastructure/clients/microservices.py:118-124`.
- Manejo de MS2 caído: `core_backend/apps/core/views.py:686-688`.
- Circuit breaker: `microservices/mole_chat/app/core/circuit_breaker.py:20-90`.
- Redis fallback: `microservices/mole_chat/app/infrastructure/adapters/redis_sensor_cache_adapter.py:55-63`.

## Delta (matriz ideal vs. estado implementado)

El requisito hace referencia explícita a Web Mining, que no está implementado. Los patrones de bajo acoplamiento sí están presentes para los microservicios existentes.

## Nota normativa / riesgo

Diseño de bajo acoplamiento alinea con disponibilidad y continuidad de servicio.

## Siguiente paso sugerido

Decisión arquitectónica: si se implementa Web Mining, integrarlo con los patrones de retry/fallback/health-check existentes.
