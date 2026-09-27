/// Banner de bloqueo de seguridad (NOM-059 / agroquímicos).
///
/// Se renderiza cuando el backend responde 403 desde SafetyValidator.
/// Colores: equivalente móvil de `bg-red-500/10 border-red-500/30`.
library;

import 'package:flutter/material.dart';

class SafetyBlockBanner extends StatelessWidget {
  const SafetyBlockBanner({
    super.key,
    required this.reason,
    this.code,
  });

  final String reason;
  final String? code;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Semantics(
      label: 'Bloqueo de seguridad',
      child: Container(
        key: const Key('safety_block_banner'),
        margin: const EdgeInsets.symmetric(vertical: 8),
        padding: const EdgeInsets.all(12),
        decoration: BoxDecoration(
          color: scheme.errorContainer,
          border: Border.all(color: scheme.error.withValues(alpha: 0.5)),
          borderRadius: BorderRadius.circular(8),
        ),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Icon(Icons.block, color: scheme.error),
            const SizedBox(width: 8),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Contenido bloqueado por seguridad',
                    style: Theme.of(context)
                        .textTheme
                        .titleSmall
                        ?.copyWith(color: scheme.onErrorContainer),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    reason,
                    style: Theme.of(context)
                        .textTheme
                        .bodyMedium
                        ?.copyWith(color: scheme.onErrorContainer),
                  ),
                  if (code != null)
                    Padding(
                      padding: const EdgeInsets.only(top: 4),
                      child: Text(
                        'Código: $code',
                        style: Theme.of(context)
                            .textTheme
                            .bodySmall
                            ?.copyWith(color: scheme.onErrorContainer),
                      ),
                    ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}
