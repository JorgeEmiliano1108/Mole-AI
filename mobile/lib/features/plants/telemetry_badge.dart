/// Badge de origen de telemetría (contrato visual F5, spec §5).
///
/// - [TelemetrySource.bleLive]: "BLE en vivo" (icono bluetooth, color primario).
/// - [TelemetrySource.server]: "Servidor" (icono nube).
/// El historial servidor es autoritativo; el dato BLE solo decora la vista.
library;

import 'package:flutter/material.dart';

import 'package:mole_ai/features/plants/plants.dart';

class TelemetrySourceBadge extends StatelessWidget {
  const TelemetrySourceBadge({super.key, required this.source});

  final TelemetrySource source;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final live = source == TelemetrySource.bleLive;
    return Semantics(
      label: live
          ? 'Origen del dato: BLE en vivo'
          : 'Origen del dato: servidor',
      child: Chip(
        avatar: Icon(
          live ? Icons.bluetooth : Icons.cloud_outlined,
          size: 18,
          color: live ? scheme.primary : scheme.onSurfaceVariant,
        ),
        label: Text(live ? 'BLE en vivo' : 'Servidor'),
        backgroundColor:
            live ? scheme.primaryContainer : scheme.surfaceContainerHighest,
        padding: EdgeInsets.zero,
        visualDensity: VisualDensity.compact,
      ),
    );
  }
}
