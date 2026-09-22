/// Tests F5 (cierre): badge de origen BLE-live vs servidor.
library;

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mole_ai/features/plants/plants.dart';
import 'package:mole_ai/features/plants/telemetry_badge.dart';

void main() {
  group('TelemetrySource (contrato visual F5)', () {
    test('servidor es el origen por defecto', () {
      final t = Telemetry.fromJson(
          {'plant_id': 'p1', 'recorded_at': '2026-01-01'});
      expect(t.source, TelemetrySource.server);
      expect(t.hasData, isTrue);
    });

    testWidgets('badge BLE en vivo', (t) async {
      await t.pumpWidget(const MaterialApp(
          home: Scaffold(
              body: TelemetrySourceBadge(
                  source: TelemetrySource.bleLive))));
      expect(find.text('BLE en vivo'), findsOneWidget);
      expect(find.byIcon(Icons.bluetooth), findsOneWidget);
      expect(
          find.bySemanticsLabel('Origen del dato: BLE en vivo'),
          findsOneWidget);
    });

    testWidgets('badge Servidor', (t) async {
      await t.pumpWidget(const MaterialApp(
          home: Scaffold(
              body: TelemetrySourceBadge(
                  source: TelemetrySource.server))));
      expect(find.text('Servidor'), findsOneWidget);
      expect(find.byIcon(Icons.cloud_outlined), findsOneWidget);
      expect(
          find.bySemanticsLabel('Origen del dato: servidor'),
          findsOneWidget);
    });
  });
}
