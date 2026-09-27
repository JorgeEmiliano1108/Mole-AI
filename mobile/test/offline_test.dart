/// Tests Fase E: caché offline con TTL y cola de diagnósticos.
library;

import 'dart:io';

import 'package:dio/dio.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mole_ai/core/notify.dart';
import 'package:mole_ai/core/offline_db.dart';
import 'package:mole_ai/core/offline_store.dart';
import 'package:mole_ai/features/species/species.dart';
import 'package:mole_ai/features/vision/vision.dart';

import 'species_test.dart' show FakeAdapter, clientWith, jsonBody;

/// Simula corte de red: el adapter lanza → Dio lo envuelve en
/// DioException sin status → ApiClient lo mapea a RetryableException.
Never offline(RequestOptions _) =>
    throw const SocketException('sin red');

Future<OfflineStore> memStore(String dir) async {
  return OfflineStore(db: MemoryOfflineDb(), filesDir: dir);
}

void main() {
  group('OfflineStore caché', () {
    test('get respeta TTL y expiración', () async {
      final dir =
          await Directory.systemTemp.createTemp('mole_off');
      final store = await memStore(dir.path);
      await store.put('k', {'a': 1});
      expect((await store.get('k'))?.payload, {'a': 1});
      expect(
          await store.get('k', ttl: const Duration(hours: 1)),
          isNotNull);
      expect(
          await store.get('k', ttl: Duration.zero), isNull);
    });
  });

  group('searchCached (contrato §2 + offline)', () {
    test(' online guarda y offline devuelve caché', () async {
      final dir =
          await Directory.systemTemp.createTemp('mole_sp');
      final store = await memStore(dir.path);
      var online = true;
      final api = clientWith(FakeAdapter((o) {
        if (!online) {
          offline(o);
        }
        return jsonBody([
          {'id': '1', 'nombre': 'Maíz', 'nombre_cientifico': 'Zea'}
        ], 200);
      }));
      final repo = SpeciesRepository(api);
      final r1 = await repo.searchCached('maiz', store);
      expect(r1.offline, isFalse);
      expect(r1.results.single.nombre, 'Maíz');
      online = false;
      final r2 = await repo.searchCached('maiz', store);
      expect(r2.offline, isTrue);
      expect(r2.results.single.nombre, 'Maíz');
    });

    test('offline sin caché relanza', () async {
      final dir =
          await Directory.systemTemp.createTemp('mole_sp2');
      final store = await memStore(dir.path);
      final api = clientWith(FakeAdapter(
          (o) => offline(o)));
      expect(() => SpeciesRepository(api).searchCached('zzz', store),
          throwsA(anything));
    });
  });

  group('Cola de diagnósticos', () {
    test('enqueue → drain sube y limpia (archivo + registro)', () async {
      final dir =
          await Directory.systemTemp.createTemp('mole_q');
      final store = await memStore(dir.path);
      final id = await store.enqueueDiagnosis([1, 2, 3], 'f.jpg');
      expect((await store.pending()).single['id'], id);
      expect(File('${dir.path}/pending_$id.jpg').existsSync(), isTrue);

      var posted = 0;
      final api = clientWith(FakeAdapter((o) {
        posted++;
        return jsonBody({'task_id': 't1'}, 202);
      }));
      final done = await VisionRepository(api).drainQueue(store);
      expect(done, 1);
      expect(posted, 1);
      expect(await store.pending(), isEmpty);
      expect(File('${dir.path}/pending_$id.jpg').existsSync(), isFalse);
    });

    test('drain se detiene sin red (conserva la cola)', () async {
      final dir =
          await Directory.systemTemp.createTemp('mole_q2');
      final store = await memStore(dir.path);
      await store.enqueueDiagnosis([9], 'g.jpg');
      final api = clientWith(FakeAdapter(
          (o) => offline(o)));
      final done = await VisionRepository(api).drainQueue(store);
      expect(done, 0);
      expect((await store.pending()), hasLength(1));
    });
  });

  group('NotifyService (B5, sin FCM)', () {
    test('show sin init no lanza (no-op agraciado)', () async {
      await NotifyService.show('t', 'b');
    });
  });

  group('Retención MRNF02 (15 días sin pérdida)', () {
    test('cola vieja no se purga sola + telemetría sin TTL sobrevive', () async {
      final dir =
          await Directory.systemTemp.createTemp('mole_ret');
      final db = MemoryOfflineDb();
      final store = OfflineStore(db: db, filesDir: dir.path);
      // Simula 15 días de telemetría (288 lecturas/día a intervalo 5min).
      final old = DateTime.now().toUtc().subtract(const Duration(days: 15));
      for (var d = 0; d < 15; d++) {
        await db.putCache(
            'mole_cache_tele:day$d',
            old.add(Duration(days: d)).toIso8601String(),
            '{"plant_id":"day$d"}');
      }
      // 15 días después, sin TTL, todo sigue legible (último conocido).
      for (var d = 0; d < 15; d++) {
        final hit = await store.get('mole_cache_tele:day$d');
        expect(hit, isNotNull, reason: 'día $d perdido');
      }
      // La cola con registros viejos tampoco se purga sola.
      await db.insertQueue({
        'id': 'viejo',
        'path': '${dir.path}/pending_viejo.jpg',
        'filename': 'v.jpg',
        'plant_id': null,
        'model_type': 'disease_detection',
        'created_at': old.toIso8601String(),
        'tries': 0,
      });
      expect((await store.pending()).map((e) => e['id']), contains('viejo'));
    });

    test('caché con TTL expira pero la cola no', () async {
      final dir =
          await Directory.systemTemp.createTemp('mole_ret2');
      final store = await memStore(dir.path);
      await store.put('k', {'a': 1});
      expect(await store.get('k'), isNotNull);
      // TTL cero = expirado para lectura; la cola, en cambio, no tiene TTL.
      expect(await store.get('k', ttl: Duration.zero), isNull);
      await store.enqueueDiagnosis([1], 'f.jpg');
      expect((await store.pending()), hasLength(1));
    });
  });

  group('Consejos offline por clase (PVU/S5)', () {
    test('put/getAdvice roundtrip', () async {
      final dir = await Directory.systemTemp.createTemp('mole_adv');
      final store = await memStore(dir.path);
      await store.putAdvice('mildiu', 'Aplicar azufre solo al atardecer.');
      expect(await store.getAdvice('mildiu'),
          'Aplicar azufre solo al atardecer.');
      expect(await store.getAdvice('roya'), isNull);
    });

    test('LRU mantiene máximo 50 entradas', () async {
      final dir = await Directory.systemTemp.createTemp('mole_adv_lru');
      final store = await memStore(dir.path);
      for (var i = 0; i < 50; i++) {
        await store.putAdvice('clase_$i', 'consejo $i');
      }
      await store.getAdvice('clase_0'); // refresca uso de la más vieja.
      await store.putAdvice('clase_nueva', 'nuevo');
      expect(await store.getAdvice('clase_0'), isNotNull);
      expect(await store.getAdvice('clase_1'), isNull);
    });
  });
}
