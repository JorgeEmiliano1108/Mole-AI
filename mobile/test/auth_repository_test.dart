/// Tests del AuthRepository (contrato §1).
library;

import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mole_ai/core/api_client.dart';
import 'package:mole_ai/core/errors.dart';
import 'package:mole_ai/core/session_store.dart';
import 'package:mole_ai/features/auth/auth_controller.dart';
import 'package:mole_ai/features/auth/auth_repository.dart';
import 'package:mole_ai/features/auth/auth_screens.dart';

import 'species_test.dart' show FakeAdapter, clientWith, jsonBody;

/// JWT sin firma para tests: el claim `role` se lee sin verificar.
String _fakeJwt(String role) {
  String enc(Object o) =>
      base64Url.encode(utf8.encode(jsonEncode(o))).replaceAll('=', '');
  return "${enc({'alg': 'HS256'})}.${enc({'role': role, 'sub': '1'})}.sig";
}

void main() {
  group('AuthRepository', () {
    test('login guarda UNA key token + rol', () async {
      String? postedUser;
      final session = MemorySessionStore();
      final api = clientWith(FakeAdapter((o) {
        postedUser = (o.data as Map?)?['username'] as String?;
        return jsonBody({'token': 'JWT', 'role': 'admin'}, 200);
      }), session: session);
      final repo = AuthRepository(api, session);
      expect(await repo.login('a@x.com', 'pw'), 'admin');
      expect(postedUser, 'a@x.com');
      expect(await session.readToken(), 'JWT');
      expect(await session.readRole(), 'admin');
    });

    test('login 401 propaga mensaje del backend', () async {
      final session = MemorySessionStore();
      final api = clientWith(FakeAdapter(
          (o) => jsonBody({'error': 'Credenciales inválidas.'}, 401)),
          session: session);
      final repo = AuthRepository(api, session);
      expect(() => repo.login('a', 'b'),
          throwsA(isA<UnauthorizedException>()));
      expect(await session.readToken(), isNull);
    });

    test('logout borra sesión aunque falle la red', () async {
      final session = MemorySessionStore()
        ..token = 'T'
        ..role = 'user';
      final api = clientWith(
          FakeAdapter((o) => jsonBody({}, 500)), session: session);
      await AuthRepository(api, session).logout();
      expect(await session.readToken(), isNull);
    });

    test('consent envía booleano estricto', () async {
      Object? sent;
      final session = MemorySessionStore();
      final api = clientWith(FakeAdapter((o) {
        sent = o.data;
        return jsonBody({'status': 'recorded'}, 200);
      }), session: session);
      await AuthRepository(api, session).setConsent(true);
      expect((sent as Map)['consent'], isTrue);
      expect((sent as Map).containsKey('ai_consent'), isFalse);
    });

    test('consentimiento IA viaja separado y opcional (S3)', () async {
      Object? sent;
      final session = MemorySessionStore();
      final api = clientWith(FakeAdapter((o) {
        sent = o.data;
        return jsonBody({'status': 'recorded'}, 200);
      }), session: session);
      await AuthRepository(api, session).setConsent(true, aiConsent: true);
      expect((sent as Map)['consent'], isTrue);
      expect((sent as Map)['ai_consent'], isTrue);
    });
  });

  group('AuthRepository.register (LFPDPPP B2)', () {
    test('envía consent:true explícito', () async {
      Object? sent;
      final session = MemorySessionStore();
      final api = clientWith(FakeAdapter((o) {
        sent = o.data;
        return jsonBody({'status': 'created'}, 201);
      }), session: session);
      await AuthRepository(api, session)
          .register('nuevo', 'Segura123!', consent: true);
      expect((sent as Map)['consent'], isTrue);
    });
  });

  group('AuthRepository.refresh (B3 sliding window)', () {
    test('guarda el token nuevo preservando el rol', () async {
      final session = MemorySessionStore()
        ..token = 'OLD'
        ..role = 'admin';
      final api = clientWith(FakeAdapter(
          (o) => jsonBody({'token': 'NEW'}, 200)),
          session: session);
      await AuthRepository(api, session).refresh();
      expect(await session.readToken(), 'NEW');
      expect(await session.readRole(), 'admin');
    });

    test('roleFromJwt: sincroniza rol elevado desde el JWT fresco', () async {
      final session = MemorySessionStore()
        ..token = 'OLD'
        ..role = 'user';
      final api = clientWith(
          FakeAdapter((o) => jsonBody({'token': _fakeJwt('admin')}, 200)),
          session: session);
      await AuthRepository(api, session).refresh();
      expect(await session.readRole(), 'admin');
    });

    test('roleFromJwt: ignora claim inválido y preserva caché', () {
      expect(roleFromJwt('opaco'), isNull);
      expect(roleFromJwt(_fakeJwt('dios')), isNull);
      expect(roleFromJwt(_fakeJwt('superuser')), 'superuser');
    });

    test('refresh prefiere campo role explícito del backend', () async {
      final session = MemorySessionStore()
        ..token = 'OLD'
        ..role = 'user';
      final api = clientWith(
          FakeAdapter(
              (o) => jsonBody({'token': _fakeJwt('user'), 'role': 'admin'}, 200)),
          session: session);
      await AuthRepository(api, session).refresh();
      expect(await session.readRole(), 'admin');
    });
  });

  group('AuthRepository.password-reset (ADR-0006)', () {
    test('request envía email (respuesta siempre 202)', () async {
      Object? sent;
      final session = MemorySessionStore();
      final api = clientWith(FakeAdapter((o) {
        sent = o.data;
        return jsonBody({'status': 'accepted'}, 202);
      }), session: session);
      await AuthRepository(api, session).requestPasswordReset('a@x.mx');
      expect((sent as Map)['email'], 'a@x.mx');
    });

    test('confirm envía token + password', () async {
      Object? sent;
      final session = MemorySessionStore();
      final api = clientWith(FakeAdapter((o) {
        sent = o.data;
        return jsonBody({'status': 'password_updated'}, 200);
      }), session: session);
      await AuthRepository(api, session)
          .confirmPasswordReset('tok123', 'Nueva123!');
      expect((sent as Map)['token'], 'tok123');
      expect((sent as Map)['new_password'], 'Nueva123!');
    });
  });

group('ConsentScreen IA (S3)', () {
  testWidgets('checkbox IA viaja en el grant', (t) async {
    Object? sent;
    final session = MemorySessionStore();
    await t.pumpWidget(ProviderScope(
      overrides: [
        apiClientProvider.overrideWithValue(clientWith(FakeAdapter((o) {
          sent = o.data;
          return jsonBody({'status': 'recorded'}, 200);
        }), session: session)),
        sessionStoreProvider.overrideWithValue(session),
      ],
      child: const MaterialApp(home: Scaffold(body: ConsentScreen())),
    ));
    await t.pump();
    await t.pump(const Duration(milliseconds: 100));
    await t.tap(find.text('Acepto el uso de IA en mis diagnósticos y chat'));
    await t.pump();
    await t.tap(find.text('Acepto el uso de mis datos'));
    await t.pump();
    await t.pump(const Duration(milliseconds: 100));
    expect((sent as Map)['consent'], isTrue);
    expect((sent as Map)['ai_consent'], isTrue);
  });

  testWidgets('token expirado durante consentimiento cierra sesión (Issue 09)',
      (t) async {
    final session = MemorySessionStore()
      ..token = 'EXPIRED'
      ..role = 'user';
    await t.pumpWidget(ProviderScope(
      overrides: [
        apiClientProvider.overrideWithValue(clientWith(FakeAdapter((o) {
          if (o.path.contains('profile') || o.path.contains('consent')) {
            return jsonBody({'detail': 'Token has expired.'}, 401);
          }
          return jsonBody({'status': 'ok'}, 200);
        }), session: session)),
        sessionStoreProvider.overrideWithValue(session),
      ],
      child: const MaterialApp(home: Scaffold(body: ConsentScreen())),
    ));
    await t.pump();
    await t.pump(const Duration(milliseconds: 100));
    expect(find.text('Acepto el uso de mis datos'), findsOneWidget);

    await t.tap(find.text('Acepto el uso de mis datos'));
    await t.pump();
    await t.pump(const Duration(milliseconds: 100));

    // LFPDPPP: no se salta consentimiento; se exige re-login.
    expect(await session.readToken(), isNull);
    final container =
        ProviderScope.containerOf(t.element(find.byType(ConsentScreen)));
    expect(container.read(authControllerProvider).status,
        AuthStatus.unauthenticated);
  });
});
}
