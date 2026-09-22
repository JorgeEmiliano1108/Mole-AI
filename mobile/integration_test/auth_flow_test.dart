/// E2E auth contra backend REAL (V1/D, sin FakeAdapter).
///
/// Requiere backend alcanzable en API_BASE_URL (`--dart-define`, default
/// emulador). Cada corrida usa usuario ÚNICO y lo borra vía DELETE profile
/// (ARCO): teardown estricto sin acceso a la DB.
/// Correr: `flutter test integration_test` (host) o `flutter drive`
/// (dispositivo). En CI solo con staging vivo (puerta documentada).
library;

import 'package:flutter_test/flutter_test.dart';
import 'package:integration_test/integration_test.dart';
import 'package:mole_ai/core/api_client.dart';
import 'package:mole_ai/core/session_store.dart';
import 'package:mole_ai/features/auth/auth_repository.dart';

void main() {
  IntegrationTestWidgetsFlutterBinding.ensureInitialized();

  group('auth E2E (backend real)', () {
    late ApiClient api;
    late MemorySessionStore session;
    late AuthRepository repo;
    late String username;
    String? token;

    setUp(() {
      session = MemorySessionStore();
      api = ApiClient(session: session);
      repo = AuthRepository(api, session);
      final stamp = DateTime.now().microsecondsSinceEpoch;
      username = 'it_$stamp';
    });

    tearDown(() async {
      // Teardown estricto: borra al usuario vía la propia API (ARCO).
      if (await session.readToken() != null) {
        try {
          await api.postJson('auth/logout/');
        } catch (_) {}
        try {
          await repo.deleteProfile();
        } catch (_) {}
      }
      await session.clear();
      token = null;
    });

    testWidgets('register→login→profile→refresh→logout', (t) async {
      await repo.register(username, 'ItSegura123!',
          email: '$username@it.mole', consent: true);
      final role = await repo.login(username, 'ItSegura123!');
      expect(role, isNotEmpty);
      token = await session.readToken();
      expect(token, isNotNull);

      final profile = await repo.profile();
      expect(profile['data_consent'], isTrue);

      final before = token;
      await repo.refresh();
      token = await session.readToken();
      expect(token, isNotNull);
      expect(token, isNot(equals(before))); // jti rotado (B3)

      await repo.logout();
      token = await session.readToken();
      expect(token, isNull);
    });
  });
}
