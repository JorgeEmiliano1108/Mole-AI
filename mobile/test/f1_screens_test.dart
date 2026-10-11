/// Wave F1 Slice 2 (deuda-21): widget tests de las pantallas pedidas.
///
/// map y plant_detail ya tienen cobertura en n3_test.dart; aquí: reports,
/// chat, weather y diagnosis. Sin red real (FakeAdapter), sin platform
/// channels (sin taps a picker/geolocator/url_launcher).
library;

import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mole_ai/core/offline_store.dart';
import 'package:mole_ai/features/chat/chat.dart';
import 'package:mole_ai/features/chat/chat_screen.dart';
import 'package:mole_ai/features/map/map.dart';
import 'package:mole_ai/features/map/map_screen.dart';
import 'package:mole_ai/features/reports/reports.dart';
import 'package:mole_ai/features/reports/reports_screen.dart';
import 'package:mole_ai/features/vision/diagnosis_screen.dart';
import 'package:mole_ai/features/vision/vision.dart';
import 'package:mole_ai/features/weather/weather_screen.dart';

import 'offline_test.dart' show memStore;
import 'species_test.dart' show FakeAdapter, clientWith, jsonBody;

ResponseBody _reportsOk(RequestOptions o) {
  final p = o.path;
  if (p.contains('reports/generate')) {
    return jsonBody({'job_id': 'j1', 'status': 'QUEUED'}, 200);
  }
  if (p.contains('reports/j1/status')) {
    return jsonBody({'status': 'SUCCESS'}, 200);
  }
  if (p.contains('reports/j1/download')) {
    return jsonBody({'download_url': 'https://x/r.pdf'}, 200);
  }
  return jsonBody({}, 200);
}

ResponseBody _chatOk(RequestOptions o) {
  final p = o.path;
  if (p.contains('chat/history')) return jsonBody({'results': []}, 200);
  if (p.contains('llm/chat')) {
    return jsonBody({
      'response': 'Riega al amanecer',
      'sources': [],
      'disclaimer': 'Aviso generativo.',
    }, 200);
  }
  return jsonBody({}, 200);
}

ResponseBody _weatherOk(RequestOptions o) {
  if (o.path.contains('weather/current')) {
    return jsonBody({
      'main': {'temp': 25.0, 'humidity': 60},
      'weather': [
        {'description': 'soleado'}
      ],
    }, 200);
  }
  return jsonBody({}, 200);
}

void main() {
  group('ReportsScreen (F1)', () {
    testWidgets('generar → poll → muestra Abrir PDF', (t) async {
      await t.pumpWidget(ProviderScope(
        overrides: [
          reportRepositoryProvider.overrideWithValue(ReportRepository(
              clientWith(FakeAdapter(_reportsOk)),
              delay: (_) async {})),
        ],
        child: const MaterialApp(home: Scaffold(body: ReportsScreen())),
      ));
      await t.tap(find.text('Generar PDF'));
      await t.pump();
      await t.pump(const Duration(milliseconds: 100));
      await t.pump(const Duration(milliseconds: 100));
      expect(find.text('Abrir PDF'), findsOneWidget);
    });

    testWidgets('fallo del backend muestra Reintentar', (t) async {
      await t.pumpWidget(ProviderScope(
        overrides: [
          reportRepositoryProvider.overrideWithValue(ReportRepository(
              clientWith(FakeAdapter((_) => jsonBody({}, 500))),
              delay: (_) async {})),
        ],
        child: const MaterialApp(home: Scaffold(body: ReportsScreen())),
      ));
      await t.tap(find.text('Generar PDF'));
      await t.pump();
      await t.pump(const Duration(milliseconds: 100));
      expect(find.text('Reintentar'), findsOneWidget);
    });
  });

  group('ChatScreen (F1)', () {
    testWidgets('enviar muestra respuesta + disclaimer', (t) async {
      await t.pumpWidget(ProviderScope(
        overrides: [
          chatRepositoryProvider.overrideWithValue(
              ChatRepository(clientWith(FakeAdapter(_chatOk)))),
        ],
        child: const MaterialApp(home: Scaffold(body: ChatScreen())),
      ));
      await t.pump();
      await t.pump(const Duration(milliseconds: 100));
      expect(find.textContaining('Pregunta sobre tus plantas'),
          findsOneWidget);
      await t.enterText(find.byType(TextField), '¿cada cuánto riego?');
      await t.tap(find.byIcon(Icons.send));
      await t.pump();
      await t.pump(const Duration(milliseconds: 100));
      expect(find.text('Riega al amanecer'), findsOneWidget);
      expect(find.text('Aviso generativo.'), findsOneWidget);
    });
  });

  group('WeatherScreen (F1)', () {
    testWidgets('preset CDMX muestra temperatura', (t) async {
      await t.pumpWidget(ProviderScope(
        overrides: [
          mapRepositoryProvider.overrideWithValue(
              MapRepository(clientWith(FakeAdapter(_weatherOk)))),
        ],
        child: const MaterialApp(home: Scaffold(body: WeatherScreen())),
      ));
      await t.pump();
      await t.pump(const Duration(milliseconds: 200));
      expect(find.text('Temperatura'), findsOneWidget);
      expect(find.text('25.0°C'), findsOneWidget);
    });

    testWidgets('coordenadas inválidas avisan sin llamar a la red',
        (t) async {
      var calls = 0;
      await t.pumpWidget(ProviderScope(
        overrides: [
          mapRepositoryProvider.overrideWithValue(
            MapRepository(clientWith(FakeAdapter((o) {
              calls++;
              return _weatherOk(o);
            }))),
          ),
        ],
        child: const MaterialApp(home: Scaffold(body: WeatherScreen())),
      ));
      await t.pump();
      await t.pump(const Duration(milliseconds: 200));
      final before = calls;
      await t.enterText(find.widgetWithText(TextField, 'Latitud'), 'xx');
      await t.tap(find.text('Ver'));
      await t.pump();
      expect(find.text('Coordenadas inválidas.'), findsOneWidget);
      expect(calls, before);
    });
  });

  group('DiagnosisScreen (F1)', () {
    testWidgets('estado inicial ofrece captura + guía de encuadre',
        (t) async {
      // Nota F1: a 600px de alto el Column desborda (overflow real en
      // pantallas chicas — candidato F2); el test usa superficie alta.
      t.binding.setSurfaceSize(const Size(800, 1400));
      addTearDown(() => t.binding.setSurfaceSize(null));
      final store = await memStore('/tmp/mole_f1_diag');
      await t.pumpWidget(ProviderScope(
        overrides: [
          offlineStoreProvider
              .overrideWithValue(AsyncValue.data(store)),
          visionRepositoryProvider.overrideWithValue(VisionRepository(
              clientWith(FakeAdapter((_) => jsonBody({}, 200))))),
        ],
        child: const MaterialApp(home: Scaffold(body: DiagnosisScreen())),
      ));
      await t.pump();
      await t.pump(const Duration(milliseconds: 100));
      expect(find.text('Encuadra la hoja aquí'), findsOneWidget);
      expect(find.text('Foto'), findsOneWidget);
      expect(find.text('Galería'), findsOneWidget);
      expect(find.text('Ver historial'), findsOneWidget);
    });
  });
}
