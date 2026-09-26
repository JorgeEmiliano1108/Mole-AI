/// Tests N-1: Mis avisos (modelo, repositorio, pantalla).
library;

import 'dart:io';

import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mole_ai/core/offline_store.dart';
import 'package:mole_ai/features/alerts/alerts.dart';
import 'package:mole_ai/features/alerts/alerts_screen.dart';

import 'offline_test.dart' show memStore;
import 'species_test.dart' show FakeAdapter, clientWith, jsonBody;

/// Sin red: el adapter lanza → DioException sin status → RetryableException.
Never _offline(RequestOptions _) =>
    throw const SocketException('sin red');

const _alertsPayload = {
  'alerts': [
    {
      'tipo': 'error',
      'msg': 'Humedad por debajo del umbral crítico (10.0%)',
      'source': 'soil',
      'recorded_at': '2026-09-26T10:00:00Z',
      'device_id': 'd1',
      'plant_id': 'p1',
    },
    {
      'tipo': 'warn',
      'msg': 'Fluctuación térmica detectada (31.0°C)',
      'source': 'ambient',
      'recorded_at': '2026-09-26T10:05:00Z',
      'device_id': 'd1',
      'plant_id': null,
    },
    {'tipo': 'info', 'msg': 'Monitor Vital estable.'},
  ]
};

/// Sin I/O real: MemoryOfflineDb ignora filesDir (createTemp colgaría
/// la zona fake-async de los widget tests, como en ux_fasec_test).
Future<OfflineStore> _store() async => memStore('/tmp/mole_alerts_test');

final List<(String, String)> notified = [];

Future<void> _record(String title, String body) async {
  notified.add((title, body));
}

Widget _wrap(Widget child,
        {required AlertsRepository repo, required OfflineStore store}) =>
    ProviderScope(
      overrides: [
        alertsRepositoryProvider.overrideWithValue(repo),
        offlineStoreProvider.overrideWithValue(AsyncValue.data(store)),
      ],
      child: MaterialApp(
          home: Scaffold(
              body: Builder(builder: (context) => child))),
    );

Widget _screen() => const AlertsScreen(
      pollInterval: Duration(hours: 1),
      onNotify: _record,
    );

AlertsRepository _repo(ResponseBody Function(RequestOptions) handler) =>
    AlertsRepository(clientWith(FakeAdapter(handler)));

void main() {
  group('PlantAlert', () {
    test('parsea severidades y campos', () {
      final a = PlantAlert.fromJson(
          (_alertsPayload['alerts'] as List).first as Map<String, dynamic>);
      expect(a.severity, AlertSeverity.error);
      expect(a.message, contains('Humedad'));
      expect(a.plantId, 'p1');
      expect(a.notifiable, isTrue);
    });

    test('defectos seguros ante backend degradado', () {
      final a = PlantAlert.fromJson({'tipo': 'rara'});
      expect(a.severity, AlertSeverity.info);
      expect(a.message, isNotEmpty);
      expect(a.notifiable, isFalse);
    });

    test('fingerprint estable para dedup', () {
      final m = (_alertsPayload['alerts'] as List).first as Map<String, dynamic>;
      expect(
          PlantAlert.fromJson(m).fingerprint, PlantAlert.fromJson(m).fingerprint);
    });
  });

  group('AlertsRepository', () {
    test('lista avisos del contrato', () async {
      final repo = AlertsRepository(
          clientWith(FakeAdapter((_) => jsonBody(_alertsPayload, 200))));
      final list = await repo.myAlerts();
      expect(list, hasLength(3));
      expect(list.first.severity, AlertSeverity.error);
    });

    test('forma inesperada → lista vacía, sin throw', () async {
      final repo = AlertsRepository(
          clientWith(FakeAdapter((_) => jsonBody({'alerts': 'x'}, 200))));
      expect(await repo.myAlerts(), isEmpty);
    });
  });

  group('AlertsScreen', () {
    testWidgets('renderiza lista con semántica por severidad', (t) async {
      await t.pumpWidget(_wrap(
        _screen(),
        repo: _repo((_) => jsonBody(_alertsPayload, 200)),
        store: await _store(),
      ));
      await t.pump();
      await t.pump(const Duration(milliseconds: 100));
      expect(find.textContaining('Humedad por debajo'), findsOneWidget);
      expect(find.textContaining('Fluctuación térmica'), findsOneWidget);
      expect(find.bySemanticsLabel('error: Humedad por debajo del umbral crítico (10.0%), 2026-09-26T10:00:00Z'),
          findsOneWidget);
      expect(
          notified
              .where((n) =>
                  n.$1 == 'Alerta en tu planta' &&
                  n.$2.contains('Humedad por debajo'))
              .length,
          1);
      expect(
          notified
              .where((n) =>
                  n.$1 == 'Aviso en tu planta' &&
                  n.$2.contains('Fluctuación'))
              .length,
          1);
      expect(notified.where((n) => n.$2.contains('estable')).length, 0);
    });

    testWidgets('vacío declara estabilidad', (t) async {
      await t.pumpWidget(_wrap(
        _screen(),
        repo: _repo((_) => jsonBody({'alerts': []}, 200)),
        store: await _store(),
      ));
      await t.pump();
      await t.pump(const Duration(milliseconds: 100));
      expect(find.text('Sin avisos. Tus plantas están estables.'), findsOneWidget);
    });

    testWidgets('error 400 muestra mensaje + reintentar', (t) async {
      await t.pumpWidget(_wrap(
        _screen(),
        repo: _repo((_) => jsonBody({'detail': 'x'}, 400)),
        store: await _store(),
      ));
      await t.pump();
      await t.pump(const Duration(milliseconds: 100));
      expect(find.text('Reintentar'), findsOneWidget);
      expect(
          find.bySemanticsLabel('Error: x'), findsOneWidget);
    });

    testWidgets('sin red sirve caché con chip offline', (t) async {
      final store = await _store();
      await store.put(OfflineStore.alertsKey(), {
        'alerts': (_alertsPayload['alerts'] as List).toList(),
      });
      await t.pumpWidget(_wrap(
        _screen(),
        repo: _repo(_offline),
        store: store,
      ));
      await t.pump();
      await t.pump(const Duration(milliseconds: 100));
      expect(find.textContaining('Sin conexión'), findsOneWidget);
      expect(find.textContaining('Humedad por debajo'), findsOneWidget);
    });
  });
}
