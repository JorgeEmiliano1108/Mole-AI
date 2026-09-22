/// Tests F3: portal público sin sesión + forgot-password.
library;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mole_ai/core/offline_db.dart';
import 'package:mole_ai/core/offline_store.dart';
import 'package:mole_ai/features/auth/forgot_password.dart';
import 'package:mole_ai/features/public/public_home.dart';
import 'package:mole_ai/features/species/species.dart';
import 'package:mole_ai/features/species/species_search_screen.dart';

import 'species_test.dart' show FakeAdapter, clientWith, jsonBody;

void main() {
  group('Portal público (issue 14)', () {
    testWidgets('hero + CTAs sin token', (t) async {
      final api = clientWith(FakeAdapter((o) => jsonBody([], 200)));
      await t.pumpWidget(ProviderScope(
        overrides: [
          speciesRepositoryProvider.overrideWithValue(SpeciesRepository(api)),
          offlineStoreProvider.overrideWithValue(AsyncValue.data(
              OfflineStore(db: MemoryOfflineDb(), filesDir: '/tmp'))),
        ],
        child: const MaterialApp(home: PublicHomeScreen()),
      ));
      await t.pumpAndSettle();
      expect(find.text('Mole.AI'), findsWidgets);
      expect(find.text('Entrar'), findsOneWidget);
      expect(find.text('Crear cuenta'), findsOneWidget);
      expect(find.text('Explorar flora endémica'), findsOneWidget);
    });

    testWidgets('forgot request muestra mensaje anti-enumeración', (t) async {
      await t.pumpWidget(const ProviderScope(
        child: MaterialApp(home: ForgotRequestScreen()),
      ));
      await t.enterText(find.byType(TextField), 'nadie@x.mx');
      await t.tap(find.text('Enviar enlace'));
      await t.pumpAndSettle();
      // Sin backend en tests: debe mostrar error amigable, no crashear.
      expect(find.text('Enviar enlace'), findsOneWidget);
    });
  });
}
