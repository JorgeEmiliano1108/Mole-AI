/// Tests N-3: a11y/offline por pantalla (mapa, detalle, knowledge).
library;

import 'dart:io';

import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mole_ai/core/offline_store.dart';
import 'package:mole_ai/features/admin/knowledge_screen.dart';
import 'package:mole_ai/features/map/map.dart';
import 'package:mole_ai/features/map/map_screen.dart';
import 'package:mole_ai/features/plants/plant_detail.dart';
import 'package:mole_ai/features/plants/plants.dart';
import 'package:mole_ai/features/plants/plants_screen.dart'
    show plantsRepositoryProvider, telemetryRepositoryProvider;

import 'offline_test.dart' show memStore;
import 'species_test.dart' show FakeAdapter, clientWith, jsonBody;

const _hotspotsPayload = {
  'hotspots': [
    {'lat': 19.4, 'lng': -99.1, 'severity': 'high', 'species': 'Maíz'}
  ]
};

const _plantPayload = {'id': 'p1', 'nickname': 'Tomate'};

const _telePayload = {
  'plant_id': 'p1',
  'recorded_at': '2026-09-26T10:00:00Z',
  'soil_humidity': 40.0,
};

ResponseBody _ok(RequestOptions o) {
  final p = o.path;
  if (p.contains('map/hotspots')) return jsonBody(_hotspotsPayload, 200);
  if (p.contains('user-plants/p1')) return jsonBody(_plantPayload, 200);
  if (p.contains('telemetry/latest')) return jsonBody(_telePayload, 200);
  return jsonBody({}, 200);
}

void main() {
  group('isIndexingTransient', () {
    test('transitorios vs terminales del backend', () {
      for (final s in ['PENDING', 'uploading', 'Uploaded', 'indexing']) {
        expect(isIndexingTransient(s), isTrue, reason: s);
      }
      for (final s in ['INDEXED', 'FAILED', 'desconocido', '']) {
        expect(isIndexingTransient(s), isFalse, reason: s);
      }
    });
  });

  group('MapScreen (issue N-3)', () {
    testWidgets('marcador anuncia especie+severidad en texto', (t) async {
      await t.pumpWidget(ProviderScope(
        overrides: [
          mapRepositoryProvider.overrideWithValue(MapRepository(
              clientWith(FakeAdapter(_ok)))),
        ],
        child: const MaterialApp(home: Scaffold(body: MapScreen())),
      ));
      await t.pump();
      await t.pump(const Duration(milliseconds: 200));
      final lab = t.getSemantics(find.byIcon(Icons.location_on)).label;
      expect(lab, contains('Maíz, severidad high'));
    });

    testWidgets('vacío declara mapa sin marcadores', (t) async {
      await t.pumpWidget(ProviderScope(
        overrides: [
          mapRepositoryProvider.overrideWithValue(MapRepository(
              clientWith(FakeAdapter(
                  (_) => jsonBody({'hotspots': []}, 200))))),
        ],
        child: const MaterialApp(home: Scaffold(body: MapScreen())),
      ));
      await t.pump();
      await t.pump(const Duration(milliseconds: 200));
      expect(find.textContaining('Sin hotspots'), findsOneWidget);
    });
  });

  group('PlantDetailScreen (issue N-3)', () {
    testWidgets('error muestra mensaje + reintentar', (t) async {
      await t.pumpWidget(ProviderScope(
        overrides: [
          plantsRepositoryProvider.overrideWithValue(PlantsRepository(
              clientWith(FakeAdapter((_) => jsonBody({}, 400))))),
          telemetryRepositoryProvider.overrideWithValue(TelemetryRepository(
              clientWith(FakeAdapter((_) => jsonBody({}, 200))))),
          offlineStoreProvider.overrideWithValue(
              AsyncValue.data(await memStore('/tmp/mole_n3_err'))),
        ],
        child: const MaterialApp(
            home: Scaffold(body: PlantDetailScreen(plantId: 'p1'))),
      ));
      await t.pump();
      await t.pump(const Duration(milliseconds: 100));
      expect(find.text('Reintentar'), findsOneWidget);
      expect(find.bySemanticsLabel('Error: Error inesperado. Intenta de nuevo.'), findsOneWidget);
    });

    testWidgets('offline sirve caché con chip', (t) async {
      Never offline(RequestOptions _) =>
          throw const SocketException('sin red');
      final store = await memStore('/tmp/mole_n3');
      await store.put(OfflineStore.telemetryKey('p1'), {
        'plant_id': 'p1',
        'recorded_at': 'ayer',
        'soil_humidity': 40.0,
      });
      await t.pumpWidget(ProviderScope(
        overrides: [
          plantsRepositoryProvider.overrideWithValue(PlantsRepository(
              clientWith(FakeAdapter(_ok)))),
          telemetryRepositoryProvider.overrideWithValue(TelemetryRepository(
              clientWith(FakeAdapter(offline)))),
          offlineStoreProvider.overrideWithValue(AsyncValue.data(store)),
        ],
        child: const MaterialApp(
            home: Scaffold(body: PlantDetailScreen(plantId: 'p1'))),
      ));
      await t.pump();
      await t.pump(const Duration(milliseconds: 100));
      expect(find.textContaining('Sin conexión'), findsOneWidget);
      expect(find.text('40.0 %'), findsOneWidget);
    });
  });
}
