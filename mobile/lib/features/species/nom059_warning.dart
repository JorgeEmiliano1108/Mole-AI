/// Aviso NOM-059 obligatorio (contrato §2, Guardrail C `enforce-compliance`).
///
/// Si la especie está protegida, este widget DEBE mostrarse con el texto
/// íntegro de `protection_warning`. Prohibido ocultarlo o resumirlo.
library;

import 'package:flutter/material.dart';

import 'species.dart';

class Nom059Warning extends StatelessWidget {
  const Nom059Warning({super.key, required this.species});

  final Species species;

  @override
  Widget build(BuildContext context) {
    if (!species.isProtected) return const SizedBox.shrink();
    final scheme = Theme.of(context).colorScheme;
    return Container(
      key: const Key('nom059_warning'),
      margin: const EdgeInsets.symmetric(vertical: 8),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        // Equivalente móvil de `bg-red-500/10 border-red-500/30` (web).
        // Fondo sólido errorContainer (sin alpha): la pareja tonal M3
        // errorContainer/onErrorContainer cumple contraste WCAG.
        color: scheme.errorContainer,
        border: Border.all(color: scheme.error.withValues(alpha: 0.5)),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Semantics(
        label: 'Aviso legal: especie protegida',
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Icon(Icons.warning_amber_rounded, color: scheme.error),
            const SizedBox(width: 8),
            Expanded(
              child: Text(
                species.protectionWarning ??
                    'Especie protegida por NOM-059-SEMARNAT. '
                        'Recolección sin autorización es ilegal.',
                style: Theme.of(context)
                    .textTheme
                    .bodyMedium
                    ?.copyWith(color: scheme.onErrorContainer),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
