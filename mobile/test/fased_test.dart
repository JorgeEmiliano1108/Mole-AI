/// Tests Fase D: chat, mapa y reportes (contrato §6).
library;

import 'package:flutter_test/flutter_test.dart';
import 'package:mole_ai/core/errors.dart';
import 'package:mole_ai/features/chat/chat.dart';
import 'package:mole_ai/features/map/map.dart';
import 'package:mole_ai/features/reports/reports.dart';

import 'species_test.dart' show FakeAdapter, clientWith, jsonBody;

void main() {
  group('ChatRepository (contrato §6)', () {
    test('send mapea response/sources/disclaimer', () async {
      String? sentKey;
      final api = clientWith(FakeAdapter((o) {
        sentKey = ((o.data as Map?)?.keys.join(','));
        return jsonBody({
          'response': 'Riega por la mañana.',
          'sources': [
            {'autor': 'Wiki', 'url': 'http://x', 'confianza': 0.9}
          ],
          'disclaimer': 'Uso agrícola informativo.'
        }, 200);
      }));
      final ans = await ChatRepository(api).send('¿cada cuánto riego?');
      expect(sentKey, 'message');
      expect(ans.response, contains('Riega'));
      expect(ans.sources.single.confianza, 0.9);
      expect(ans.disclaimer, contains('informativo'));
    });

    test('history mapea turnos', () async {
      final api = clientWith(FakeAdapter((o) => jsonBody({
            'results': [
              {'prompt': 'hola', 'response': 'buenas'}
            ]
          }, 200)));
      final h = await ChatRepository(api).history();
      expect(h.single.prompt, 'hola');
    });
  });

  group('MapRepository (contrato §6)', () {
    test('hotspots mapea lat/lng/severidad', () async {
      final api = clientWith(FakeAdapter((o) => jsonBody({
            'hotspots': [
              {'lat': 19.4, 'lng': -99.1, 'severity': 'high', 'species': 'Maíz'}
            ]
          }, 200)));
      final hs = await MapRepository(api).hotspots();
      expect(hs.single.severity, 'high');
      expect(hs.single.lat, 19.4);
    });

    test('weather tolera forma OpenWeather', () async {
      final api = clientWith(FakeAdapter((o) => jsonBody({
            'main': {'temp': 22.5, 'humidity': 60},
            'weather': [
              {'description': 'despejado'}
            ]
          }, 200)));
      final w = await MapRepository(api).currentWeather(19.4, -99.1);
      expect(w.temp, 22.5);
      expect(w.description, 'despejado');
    });
  });

  group('ReportRepository (contrato §6, MS3)', () {
    test('sin trailing slash en rutas exactas MS3', () async {
      final seen = <String>[];
      final api = clientWith(FakeAdapter((o) {
        seen.add(o.path);
        if (o.path.endsWith('generate')) {
          return jsonBody({'job_id': 'j1', 'status': 'QUEUED'}, 200);
        }
        return jsonBody({'status': 'SUCCESS'}, 200);
      }));
      final repo = ReportRepository(api, delay: (_) async {});
      final job = await repo.generate(dateRangeDays: 30);
      expect(job, 'j1');
      await repo.pollStatus(job);
      expect(seen.every((p) => !p.endsWith('/')), isTrue);
    });

    test('poll aborta en FAILURE con el error del job', () async {
      var calls = 0;
      final api = clientWith(FakeAdapter((o) {
        calls++;
        if (o.path.endsWith('generate')) {
          return jsonBody({'job_id': 'j9', 'status': 'QUEUED'}, 200);
        }
        return jsonBody({'status': 'FAILURE', 'error': 'sin datos'}, 200);
      }));
      final repo = ReportRepository(api, delay: (_) async {});
      final job = await repo.generate();
      await expectLater(
          repo.pollStatus(job), throwsA(isA<ApiException>()));
      expect(calls, 2);
    });

    test('downloadUrl exige http', () async {
      final api = clientWith(
          FakeAdapter((o) => jsonBody({'download_url': 'no-url'}, 200)));
      expect(() => ReportRepository(api).downloadUrl('j'),
          throwsA(isA<ApiException>()));
    });
  });
}
