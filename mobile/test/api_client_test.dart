/// Tests del ApiClient contra el contrato §0/§1/§7 (sin red).
library;

import 'package:dio/dio.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mole_ai/core/errors.dart';
import 'package:mole_ai/core/session_store.dart';

import 'species_test.dart' show FakeAdapter, clientWith, jsonBody;

void main() {
  group('ApiClient', () {
    test('agrega / final y Bearer salvo rutas públicas', () async {
      final seen = <String, String?>{};
      final session = MemorySessionStore()
        ..token = 'TOK'
        ..role = 'user';
      final api = clientWith(
          FakeAdapter((o) {
            seen[o.path] = o.headers['Authorization'] as String?;
            return jsonBody({'ok': true}, 200);
          }),
          session: session);
      // Portal público (issue 14): search sin Bearer.
      await api.getJson('plants/search');
      expect(seen.keys.single, endsWith('plants/search/'));
      expect(seen.values.single, isNull);
      // Ruta protegida: Bearer sí.
      await api.getJson('user-plants/');
      expect(seen['user-plants/'], 'Bearer TOK');

      await api.postJson('auth/login', data: {'username': 'a'});
      expect(seen['https://x/api/v1/auth/login/'], isNull);
    });

    test('401 → refresh una vez y reintenta', () async {
      final calls = <String>[];
      var n = 0;
      final session = MemorySessionStore()
        ..token = 'OLD'
        ..role = 'user';
      final api = clientWith(
          FakeAdapter((o) {
            calls.add(o.path);
            if (o.path.endsWith('auth/refresh/')) {
              return jsonBody({'token': 'NEW'}, 200);
            }
            n++;
            if (n == 1) return jsonBody({'detail': 'expired'}, 401);
            return jsonBody({'ok': true}, 200);
          }),
          session: session);
      final body = await api.getJson('user-plants/');
      expect(body['ok'], isTrue);
      expect(await session.readToken(), 'NEW');
      expect(calls.where((c) => c.endsWith('auth/refresh/')), hasLength(1));
    });

    test('401 en refresh → UnauthorizedException (ir a login)', () async {
      final session = MemorySessionStore()
        ..token = 'OLD'
        ..role = 'user';
      final api = clientWith(
          FakeAdapter((o) => jsonBody({'detail': 'bad'}, 401)),
          session: session);
      expect(() => api.getJson('user-plants/'),
          throwsA(isA<UnauthorizedException>()));
    });

    test('429 → RateLimitedException, 502 → RetryableException', () async {
      var api = clientWith(
          FakeAdapter((o) => jsonBody({'detail': 'slow'}, 429)));
      expect(() => api.getJson('llm/chat/'),
          throwsA(isA<RateLimitedException>()));

      api = clientWith(
          FakeAdapter((o) => jsonBody({'detail': 'up'}, 502)));
      expect(
          () => api.getJson('weather/current/'),
          throwsA(isA<RetryableException>()));
    });

    test('400 expone mensaje del backend', () async {
      final api = clientWith(FakeAdapter(
          (o) => jsonBody({'error': 'Credenciales inválidas.'}, 401)));
      // En auth/* no hay refresh: el 401 llega directo como Unauthorized.
      try {
        await api.postJson('auth/login/', data: {});
        fail('debió lanzar');
      } on UnauthorizedException catch (e) {
        expect(e.message, contains('Credenciales'));
      }
    });

    test('ping true solo con status healthy', () async {
      var api = clientWith(
          FakeAdapter((o) => jsonBody({'status': 'healthy'}, 200)));
      expect(await api.ping(), isTrue);
      api = clientWith(FakeAdapter((o) => jsonBody({}, 500)));
      expect(await api.ping(), isFalse);
    });
  });

  group('ApiClient.deleteJson (ARCO/teardown)', () {
    test('204 vacío → {} sin romper cast', () async {
      final api = clientWith(FakeAdapter(
          (o) => ResponseBody.fromString('', 204)));
      expect(await api.deleteJson('auth/profile/'), isEmpty);
    });
  });
}
