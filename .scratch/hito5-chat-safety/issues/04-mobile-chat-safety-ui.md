# 04-mobile-chat-safety-ui

Status: ready-for-agent

## Título
UI Flutter: renderizar `SafetyBlockBanner` en el historial de chat ante bloqueo

## Descripción
Extender `ChatAnswer` para soportar respuestas bloqueadas y mostrar el banner rojo dentro del turno de chat, sin crash ni `_error` genérico.

## Tareas
1. `ChatAnswer`: añadir `isSafetyBlocked`, `safetyCode`, `safetyReason`.
2. `ChatRepository.send`: detectar `ApiException` con status 403 y construir `ChatAnswer` bloqueada desde `details`.
3. `ChatScreen._send`: en 403, añadir un `ChatTurn` con la respuesta bloqueada en lugar de solo `_error`.
4. `ChatScreen.build`: cuando `answer.isSafetyBlocked`, renderizar `SafetyBlockBanner` dentro de la Card.
5. Tests en `mobile/test/chat_safety_block_test.dart`.

## Criterios de aceptación
- `flutter test` verde.
- `flutter analyze` sin nuevos warnings.
