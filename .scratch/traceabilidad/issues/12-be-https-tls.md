# 12: RNF-BE-02: Seguridad perimetral HTTPS/TLS

Status: completed

## Requisito

- **ID:** RNF-BE-02
- **Capa:** Backend
- **Tipo:** RNF
- **Texto:** Todas las comunicaciones hacia los endpoints deben forzar el uso de HTTPS con certificados TLS. Las peticiones no autorizadas deben ser bloqueadas inmediatamente.

## Veredicto

✅ CERRADO PARA MVP — HTTPS forzado por defecto en producción con exenciones para probes.

## Evidencia

- HSTS/cookies seguras: `core_backend/mole_ai_backend/settings.py:67-71`.
- `IsAuthenticated` global: `core_backend/mole_ai_backend/settings.py:207`.
- JWT/Hardware auth + 401: `core_backend/apps/authentication/middleware.py:127-229`, `core_backend/apps/core/views.py:120-148`.
- `SECURE_SSL_REDIRECT` default `True` en producción (`DEBUG=False`) y `False` en desarrollo (`settings.py:72-77`).
- Exenciones de redirect para healthchecks y schema: `SECURE_REDIRECT_EXEMPT = [r'^health/$', r'^api/schema/$']`.

## Delta (matriz ideal vs. estado implementado)

El backend ya no depende exclusivamente del proxy para forzar HTTPS. Los probes de balanceadores y el schema público quedan exentos para no romper CI/healthchecks.

## Nota normativa / riesgo

LFPDPPP/MASVS-NETWORK: cifrado en tránsito forzado por defecto; la terminación TLS sigue en Nginx/ALB.

## Siguiente paso sugerido

- Verificar en staging que load balancers sigan viendo `/health/` como 200 HTTP.
- Coordinar con `deuda-fase5/13-ingress-lan-hsts.md` para compose LAN/HSTS.
