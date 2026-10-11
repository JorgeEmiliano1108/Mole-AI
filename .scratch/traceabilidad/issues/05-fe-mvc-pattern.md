# 05: RNF-FE-01: Patrón arquitectónico MVC

Status: ready-for-agent

## Requisito

- **ID:** RNF-FE-01
- **Capa:** Frontend
- **Tipo:** RNF
- **Texto:** El frontend debe implementarse bajo el patrón Modelo-Vista-Controlador (MVC) para asegurar una separación estricta entre la lógica de presentación y las reglas de negocio.

## Veredicto

❌ NO IMPLEMENTADO — La app usa Riverpod + StatefulWidget, no MVC clásico.

## Evidencia

- `mobile/lib/features/auth/auth_controller.dart:58` usa `Notifier<AuthState>`.
- `mobile/lib/features/vision/diagnosis_screen.dart:34-232` mezcla picking, conectividad, polling, edge AI y renderizado.
- Existen repositorios (`VisionRepository`, `PlantsRepository`, etc.) pero no capa Controller/View MVC.

## Delta (matriz ideal vs. estado implementado)

Tesis §4.3.1 describe un 'modelo de provider inyectable', no MVC. El código coincide con la tesis, no con la matriz.

## Nota normativa / riesgo

La separación por repositorios facilita tests y auditoría; la ausencia de MVC estricto no introduce brecha de seguridad directa.

## Siguiente paso sugerido

Refactorizar a MVC estricto o actualizar la matriz/tesis para reflejar Riverpod + repositorios como patrón real.
