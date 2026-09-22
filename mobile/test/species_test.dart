/// Tests del contrato §2: modelo Species + aviso NOM-059 obligatorio.
library;

import 'dart:convert';
import 'dart:typed_data';

import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mole_ai/core/api_client.dart';
import 'package:mole_ai/core/session_store.dart';
import 'package:mole_ai/features/species/nom059_warning.dart';
import 'package:mole_ai/features/species/species.dart';

/// Adaptador falso: responde según handler sin red.
class FakeAdapter implements HttpClientAdapter {
  FakeAdapter(this.handler);
  final ResponseBody Function(RequestOptions) handler;

  @override
  Future<ResponseBody> fetch(RequestOptions options,
          Stream<Uint8List>? s, Future<void>? c) async =>
      handler(options);

  @override
  void close({bool force = false}) {}
}

ResponseBody jsonBody(Object data, int status) => ResponseBody.fromString(
      jsonEncode(data),
      status,
      headers: {
        Headers.contentTypeHeader: [Headers.jsonContentType]
      },
    );

ApiClient clientWith(FakeAdapter adapter, {SessionStore? session}) {
  final dio = Dio()..httpClientAdapter = adapter;
  return ApiClient(
      session: session ?? MemorySessionStore(), dio: dio, baseUrl: 'https://x/api/v1/');
}

void main() {
  group('Species.fromJson', () {
    test('parsea campos del contrato §2', () {
      final s = Species.fromJson({
        'id': 'abc',
        'nombre': 'Maíz',
        'nombre_cientifico': 'Zea mays',
        'descripcion': 'd',
        'category': 'cultivo',
        'humedad': '40-60%',
        'temperatura': '20-30°C',
        'ph': '6.0-7.0',
        'image_url': 'http://img/x.png',
      });
      expect(s.nombre, 'Maíz');
      expect(s.isProtected, isFalse);
    });

    test('detecta especie protegida NOM-059', () {
      final s = Species.fromJson({
        'id': 'p1',
        'nombre': 'Biznaga',
        'nombre_cientifico': 'Echinocactus',
        'is_protected_nom059': true,
        'protection_warning': 'ATENCIÓN: Especie protegida',
        'protection_category': 'P',
      });
      expect(s.isProtected, isTrue);
      expect(s.protectionWarning, contains('ATENCIÓN'));
      expect(s.protectionCategory, 'P');
    });
  });

  group('SpeciesRepository.search', () {
    test('q vacía no llama a la red (el backend daría 400)', () async {
      var calls = 0;
      final api = clientWith(FakeAdapter((o) {
        calls++;
        return jsonBody([], 200);
      }));
      final repo = SpeciesRepository(api);
      expect(await repo.search(), isEmpty);
      expect(await repo.search(q: '  '), isEmpty);
      expect(calls, 0);
    });

    test('mapea lista del backend', () async {
      final api = clientWith(FakeAdapter(
          (o) => jsonBody([
                {'id': '1', 'nombre': 'A', 'nombre_cientifico': 'a'},
                {
                  'id': '2',
                  'nombre': 'B',
                  'nombre_cientifico': 'b',
                  'is_protected_nom059': true,
                  'protection_warning': 'W'
                },
              ], 200)));
      final repo = SpeciesRepository(api);
      final results = await repo.search(q: 'a');
      expect(results, hasLength(2));
      expect(results[1].isProtected, isTrue);
    });
  });

  group('Nom059Warning (compliance obligatorio)', () {
    testWidgets('muestra el texto íntegro si protegida', (t) async {
      final s = Species.fromJson({
        'id': 'p1',
        'nombre': 'Biznaga',
        'nombre_cientifico': 'Echinocactus',
        'is_protected_nom059': true,
        'protection_warning': 'ATENCIÓN: texto legal íntegro',
      });
      await t.pumpWidget(
          MaterialApp(home: Scaffold(body: Nom059Warning(species: s))));
      expect(find.byKey(const Key('nom059_warning')), findsOneWidget);
      expect(find.text('ATENCIÓN: texto legal íntegro'), findsOneWidget);
    });

    testWidgets('no renderiza nada si no protegida', (t) async {
      final s = Species.fromJson(
          {'id': '1', 'nombre': 'Maíz', 'nombre_cientifico': 'Zea mays'});
      await t.pumpWidget(
          MaterialApp(home: Scaffold(body: Nom059Warning(species: s))));
      expect(find.byKey(const Key('nom059_warning')), findsNothing);
    });
  });
}
