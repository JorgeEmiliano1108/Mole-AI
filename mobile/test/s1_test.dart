/// Tests S1 (normativa móvil): SQLCipher, pinning, fail-closed.
library;

import 'dart:convert';

import 'package:flutter_test/flutter_test.dart';
import 'package:mole_ai/core/api_client.dart';
import 'package:mole_ai/core/lab_ca.dart';
import 'package:mole_ai/core/offline_db.dart';
import 'package:mole_ai/core/offline_store.dart';
import 'package:mole_ai/core/session_store.dart';

class _MemKeyStore implements DbKeyStore {
  String? value;
  @override
  Future<String?> readDbKey() async => value;
  @override
  Future<void> writeDbKey(String v) async => value = v;
}

void main() {
  group('SQLCipher S1', () {
    test('generateDbPassword: 32 bytes únicos en base64url', () {
      final a = generateDbPassword();
      final b = generateDbPassword();
      expect(base64Url.decode(a), hasLength(32));
      expect(a, isNot(equals(b)));
    });

    test('resolveDbPassword: genera una vez y reutiliza', () async {
      final store = _MemKeyStore();
      final first = await resolveDbPassword(store: store);
      final second = await resolveDbPassword(store: store);
      expect(first, isNotEmpty);
      expect(second, equals(first));
    });

    test('isNotADatabaseMessage detecta fichero en plano', () {
      expect(
          SqfliteOfflineDb.isNotADatabaseMessage(
              'DatabaseException(file is not a database (code 26))'),
          isTrue);
      expect(SqfliteOfflineDb.isNotADatabaseMessage('disk I/O error'),
          isFalse);
    });

    test('lab_ca.pem es un certificado PEM válido', () {
      expect(kLabCaPem, contains('-----BEGIN CERTIFICATE-----'));
      expect(kLabCaPem, contains('-----END CERTIFICATE-----'));
    });
  });

  group('Pinning fail-closed S1', () {
    test('http con enforceHttps:true truena (no degrada a plano)', () {
      expect(
          () => ApiClient(
              session: MemorySessionStore(),
              baseUrl: 'http://10.0.2.2:8000/api/v1/',
              enforceHttps: true),
          throwsStateError);
    });

    test('http sin enforce permite dev/emulador', () {
      expect(
          () => ApiClient(
              session: MemorySessionStore(),
              baseUrl: 'http://10.0.2.2:8000/api/v1/',
              enforceHttps: false),
          returnsNormally);
    });

    test('labCaPem instala adapter propio (pinning activo)', () {
      final api = ApiClient(
          session: MemorySessionStore(),
          baseUrl: 'https://mole-edge.local:8443/api/v1/',
          enforceHttps: false,
          labCaPem: kLabCaPem);
      expect(api.httpAdapterIsPinned, isTrue);
    });

    test('sin labCaPem no se toca el adapter (tests intactos)', () {
      final api = ApiClient(
          session: MemorySessionStore(),
          baseUrl: 'https://x/api/v1/',
          enforceHttps: false);
      expect(api.httpAdapterIsPinned, isFalse);
    });
  });
}
