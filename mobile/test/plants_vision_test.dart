/// Tests de plantas/telemetría (contrato §3, §4) y visión async (§5).
library;

import 'package:dio/dio.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mole_ai/core/errors.dart';
import 'package:mole_ai/features/plants/plants.dart';
import 'package:mole_ai/features/vision/vision.dart';

import 'species_test.dart' show FakeAdapter, clientWith, jsonBody;

void main() {
  group('PlantsRepository (contrato §4)', () {
    test('my-collection mapea array directo', () async {
      final api = clientWith(FakeAdapter((o) => jsonBody([
            {
              'id': '11111111-1111-1111-1111-111111111111',
              'nickname': 'Jitomate 1',
              'species_id': null,
              'created_at': '2026-09-01T10:00:00Z'
            }
          ], 200)));
      final plants = await PlantsRepository(api).myCollection();
      expect(plants, hasLength(1));
      expect(plants.single.nickname, 'Jitomate 1');
    });

    test('user-plants desempaqueta envelope {results,count}', () async {
      final api = clientWith(FakeAdapter((o) => jsonBody({
            'results': [
              {'id': 'u1', 'nickname': 'A'}
            ],
            'count': 1
          }, 200)));
      final plants = await PlantsRepository(api).listPlants();
      expect(plants.single.id, 'u1');
    });
  });

  group('TelemetryRepository (contrato §3)', () {
    test('latest parsea doubles nulos y hasData', () async {
      final api = clientWith(FakeAdapter((o) => jsonBody({
            'plant_id': 'p1',
            'recorded_at': '2026-09-17T10:00:00Z',
            'soil_humidity': 42.5,
            'air_temperature': 23.7,
            'uv_index': null,
            'ph_level': 6.4,
          }, 200)));
      final t = await TelemetryRepository(api).latest('p1');
      expect(t.hasData, isTrue);
      expect(t.soilHumidity, 42.5);
      expect(t.uvIndex, isNull);
    });

    test('deviceHealth mapea ambient/soil/sre', () async {
      final api = clientWith(FakeAdapter((o) => jsonBody({
            'device_id': 'd1',
            'device_name': 'ESP32-A',
            'status': 'online',
            'last_seen_delta_seconds': 42,
            'ambient': {'air_temperature': 25.0, 'recorded_at': 'x'},
            'soil': [
              {'pin': '34', 'plant_nickname': 'J1', 'soil_humidity': 40.0}
            ],
            'sre_metrics': {'uptime_pct_24h': 99.8},
          }, 200)));
      final h = await TelemetryRepository(api).deviceHealth('d1');
      expect(h.ambient?.airTemperature, 25.0);
      expect(h.soil.single.pin, '34');
      expect(h.sreMetrics['uptime_pct_24h'], 99.8);
    });
  });

  group('VisionRepository (contrato §5, vía async)', () {
    test('submit envía multipart y exige task_id', () async {
      var isForm = false;
      final api = clientWith(FakeAdapter((o) {
        isForm = o.data is FormData;
        return jsonBody(
            {'status': 'processing', 'task_id': 't123'}, 202);
      }));
      final taskId = await VisionRepository(api)
          .submitDiagnosis([0xFF, 0xD8], 'foto.jpg');
      expect(isForm, isTrue);
      expect(taskId, 't123');
    });

    test('submit sin task_id lanza ApiException', () async {
      final api = clientWith(
          FakeAdapter((o) => jsonBody({'status': 'processing'}, 202)));
      expect(() => VisionRepository(api).submitDiagnosis([1], 'f.jpg'),
          throwsA(isA<ApiException>()));
    });

    test('pollStatus reintenta con backoff hasta success', () async {
      final waits = <Duration>[];
      var calls = 0;
      final api = clientWith(FakeAdapter((o) {
        calls++;
        if (calls < 3) return jsonBody({'status': 'pending'}, 200);
        return jsonBody({
          'status': 'success',
          'state': 'SUCCESS',
          'result': {
            'diagnosis': {
              'species_common': 'Jitomate',
              'severity': 'medium',
              'confidence': 0.87,
              'ph_predicted': 6.2,
              'immediate_actions': ['Ventilar'],
              'disclaimer': 'D'
            }
          }
        }, 200);
      }));
      final repo = VisionRepository(api, delay: (d) async => waits.add(d));
      final st = await repo.pollStatus('t123');
      expect(calls, 3);
      expect(st.isSuccess, isTrue);
      expect(st.diagnosis?.confidence, 0.87);
      expect(waits, [const Duration(seconds: 2), const Duration(seconds: 4)]);
    });

    test('pollStatus propaga failure sin reintentar de más', () async {
      var calls = 0;
      final api = clientWith(FakeAdapter((o) {
        calls++;
        return jsonBody(
            {'status': 'failure', 'error': 'MS1 caído'}, 200);
      }));
      final st = await VisionRepository(api, delay: (_) async {}).pollStatus('t');
      expect(calls, 1);
      expect(st.isFailure, isTrue);
      expect(st.error, 'MS1 caído');
    });
  });
}
