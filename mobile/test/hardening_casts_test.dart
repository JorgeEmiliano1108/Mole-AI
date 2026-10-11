/// Wave F1 (deuda-21): parseo defensivo, nunca casts que revienten.
///
/// TDD: estos tests fallan contra el código actual (`as String`/`as int`
/// ante cuerpos malformados lanzan TypeError). El fix los vuelve verdes
/// lanzando [ApiException] tipada en su lugar.
library;

import 'package:flutter_test/flutter_test.dart';
import 'package:mole_ai/core/errors.dart';
import 'package:mole_ai/core/session_store.dart';
import 'package:mole_ai/features/admin/admin.dart';
import 'package:mole_ai/features/auth/auth_repository.dart';
import 'package:mole_ai/features/map/map.dart';

import 'species_test.dart' show FakeAdapter, clientWith, jsonBody;

void main() {
  group('AuthRepository parseo defensivo (F1)', () {
    test('login 200 sin token lanza ApiException, no TypeError', () async {
      final session = MemorySessionStore();
      final api = clientWith(
          FakeAdapter((o) => jsonBody({'role': 'user'}, 200)),
          session: session);
      await expectLater(
        AuthRepository(api, session).login('a', 'b'),
        throwsA(isA<ApiException>()),
      );
      expect(await session.readToken(), isNull);
    });

    test('refresh 200 sin token lanza ApiException, no TypeError', () async {
      final session = MemorySessionStore()
        ..token = 'OLD'
        ..role = 'user';
      final api = clientWith(
          FakeAdapter((o) => jsonBody({}, 200)),
          session: session);
      await expectLater(
        AuthRepository(api, session).refresh(),
        throwsA(isA<ApiException>()),
      );
      expect(await session.readToken(), 'OLD');
    });

    test('password-reset 501 se propaga como ApiException (contrato §1)',
        () async {
      final session = MemorySessionStore();
      final api = clientWith(
          FakeAdapter((o) => jsonBody(
              {'error': 'Recuperación por correo no disponible.'}, 501)),
          session: session);
      Object? err;
      try {
        await AuthRepository(api, session).requestPasswordReset('a@x.mx');
      } catch (e) {
        err = e;
      }
      expect(err, isA<ApiException>());
      expect((err as ApiException).statusCode, 501);
    });
  });

  group('parseUploadGrant (F1)', () {
    test('cuerpo sin presigned_url lanza ApiException, no TypeError', () {
      expect(
        () => parseUploadGrant(const {'record_id': 'r1'}),
        throwsA(isA<ApiException>()),
      );
    });

    test('cuerpo sin record_id lanza ApiException', () {
      expect(
        () => parseUploadGrant(const {'presigned_url': 'https://s3/x'}),
        throwsA(isA<ApiException>()),
      );
    });

    test('cuerpo válido devuelve tupla', () {
      final g = parseUploadGrant(const {
        'presigned_url': 'https://s3/x',
        'record_id': 'r1',
      });
      expect(g.presignedUrl, 'https://s3/x');
      expect(g.recordId, 'r1');
    });
  });

  group('Hotspot.tryParse (F1)', () {
    test('lat/lng ausentes → null en vez de TypeError', () {
      expect(Hotspot.tryParse(const {'severity': 'high'}), isNull);
      expect(
          Hotspot.tryParse(const {'lat': 'x', 'lng': -99.1}), isNull);
    });

    test('hotspots() salta entradas inválidas sin romper la lista', () async {
      final api = clientWith(FakeAdapter((o) => jsonBody({
            'hotspots': [
              {'lat': 19.4, 'lng': -99.1, 'severity': 'high'},
              {'severity': 'low'},
            ]
          }, 200)));
      final hs = await MapRepository(api).hotspots();
      expect(hs, hasLength(1));
      expect(hs.single.severity, 'high');
    });
  });
}
