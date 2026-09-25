# Issue 13: Ingress LAN + HSTS/duckdns sincerado

Status: ready-for-agent
Sev: P1 · Área: infra · Fase: D

## Evidencia
- `docker-compose.yml:24` `127.0.0.1:8080:80` (solo loopback) vs
  `verify-staging.sh:8` `BASE_URL=http://<IP-PC>:8000` y `wait-for-services.sh:16-23`.
- `nginx.conf:34-35` HSTS comentado, bloque 443 `:186-212` comentado;
  `mole_ai_ssl.conf` termina en `mole-ia.duckdns.org` muerto (staging inalcanzable).

## Problema
LAN inalcanzable (bloquea prueba en teléfono); superficie TLS/CORS no válida.

## Aceptación
- Override LAN documentado (no commitear binds LAN) o compose LAN explícito;
  `verify-staging.sh` coherente con el bind real.
- HSTS/443: activar con cert local o documentar como no-objetivo con ADR.
- duckdns: eliminar referencias o marcar muerto en docs.

## Compliance
Superficie de red declarada y reproducible.

## Comments
(none)
