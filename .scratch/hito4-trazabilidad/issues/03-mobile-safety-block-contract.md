# 03-mobile-safety-block-contract

Status: ready-for-agent

## Título
Contrato y UI Flutter para diagnóstico de visión bloqueado por seguridad

## Descripción
Extender el contrato de polling de visión y el parser móvil para reconocer el campo `safety_block`. Cuando llegue, renderizar el `SafetyBlockBanner` existente en `DiagnosisScreen` en lugar del resultado clínico.

## Tareas
1. Actualizar `docs/mobile-contract.md` §5: documentar `result.safety_block {code, reason}` en `GET ai/vision/status/<id>/`.
2. Actualizar `docs/contracts/openapi.yml` snapshot con el nuevo campo.
3. En `mobile/lib/features/vision/vision.dart`:
   - `VisionStatus.fromJson` parsea `result.safety_block`.
   - Exponer `bool isSafetyBlocked` y `String? safetyReason`, `String? safetyCode`.
4. En `mobile/lib/features/vision/diagnosis_screen.dart`:
   - Si `isSafetyBlocked`, mostrar `SafetyBlockBanner(reason, code)`.
   - No encolar el diagnóstico ni mostrar acciones clínicas.
5. Tests en `mobile/test/vision_safety_block_test.dart`.

## Criterios de aceptación
- `flutter test` verde.
- Solo infos preexistentes en `flutter analyze`.
