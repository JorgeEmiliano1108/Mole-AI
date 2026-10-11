/// Wave F2 (N-1 + N-3): badge en NavigationBar, unread persistido,
/// dedup por id, retry + chip offline en clima.
///
/// TDD: rojo contra el código actual (sin store persistente, sin badge en
/// NavBar, sin reintento en WeatherScreen).
library;

import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mole_ai/features/alerts/alerts.dart';
import 'package:mole_ai/features/map/map.dart';
import 'package:mole_ai/features/map/map_screen.dart'
    show mapRepositoryProvider;
import 'package:mole_ai/features/weather/weather_screen.dart';
import 'package:mole_ai/home_shell.dart' show alertsDestination;
import 'package:shared_preferences/shared_preferences.dart';

import 'species_test.dart' show FakeAdapter, clientWith, jsonBody;

void main() {
  group('UnreadAlerts persistido (N-1)', () {
    test('add sobrevive recreación del store', () async {
      SharedPreferences.setMockInitialValues({});
      final prefs = await SharedPreferences.getInstance();
      final store = UnreadAlertsStore(prefs: prefs);
      await store.save(3);
      // Nueva instancia (reinicio de app) lee lo persistido.
      final fresh =
          UnreadAlertsStore(prefs: await SharedPreferences.getInstance());
      expect(await fresh.load(), 3);
    });

    test('load sin valor previo es 0', () async {
      SharedPreferences.setMockInitialValues({});
      final store = UnreadAlertsStore(
          prefs: await SharedPreferences.getInstance());
      expect(await store.load(), 0);
    });
  });

  group('PlantAlert.id (N-1 dedup por id)', () {
    test('id estable y derivado documentado', () {
      const j = {
        'tipo': 'error',
        'msg': 'Humedad baja',
        'source': 'soil',
        'recorded_at': 't1',
        'device_id': 'd1',
        'plant_id': 'p1',
      };
      final a = PlantAlert.fromJson(j);
      final b = PlantAlert.fromJson(j);
      expect(a.id, isNotEmpty);
      expect(a.id, b.id);
    });
  });

  group('alertsDestination (N-1 badge en NavigationBar)', () {
    test('sin no-leídos: icono plano', () {
      final d = alertsDestination(0);
      expect(d.label, 'Avisos');
      expect(d.icon, isNot(isA<Badge>()));
    });

    test('con no-leídos: Badge con conteo', () {
      final d = alertsDestination(4);
      expect(d.icon, isA<Badge>());
      expect((d.icon as Badge).label as Text, isNotNull);
    });
  });

  group('WeatherScreen retry + offline (N-3)', () {
    testWidgets('error 500 muestra Reintentar y reintenta', (t) async {
      var calls = 0;
      await t.pumpWidget(ProviderScope(
        overrides: [
          mapRepositoryProvider.overrideWithValue(MapRepository(
              clientWith(FakeAdapter((o) {
            calls++;
            return jsonBody({}, 500);
          })))),
        ],
        child: const MaterialApp(home: Scaffold(body: WeatherScreen())),
      ));
      await t.pump();
      await t.pump(const Duration(milliseconds: 200));
      expect(find.text('Reintentar'), findsOneWidget);
      await t.tap(find.text('Reintentar'));
      await t.pump();
      await t.pump(const Duration(milliseconds: 200));
      expect(calls, 2);
    });

    testWidgets('sin red muestra chip offline', (t) async {
      await t.pumpWidget(ProviderScope(
        overrides: [
          mapRepositoryProvider.overrideWithValue(MapRepository(
              clientWith(FakeAdapter(
                  (_) => throw const SocketException('sin red'))))),
        ],
        child: const MaterialApp(home: Scaffold(body: WeatherScreen())),
      ));
      await t.pump();
      await t.pump(const Duration(milliseconds: 200));
      expect(find.textContaining('Sin conexión'), findsOneWidget);
    });
  });
}
