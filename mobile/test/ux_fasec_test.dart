/// Tests UX Fase C: validación de login y mensajes de error amigables.
library;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mole_ai/core/errors.dart';
import 'package:mole_ai/core/offline_db.dart';
import 'package:mole_ai/core/offline_store.dart';
import 'package:mole_ai/core/session_store.dart';
import 'package:mole_ai/features/auth/auth_controller.dart';
import 'package:mole_ai/features/auth/auth_screens.dart';
import 'package:mole_ai/features/species/species.dart';
import 'package:mole_ai/features/species/species_search_screen.dart';

import 'species_test.dart' show FakeAdapter, clientWith, jsonBody;

void main() {
  group('Login (Fase C)', () {
    testWidgets('no envía vacío: muestra Requerido', (t) async {
      await t.pumpWidget(ProviderScope(
        overrides: [
          sessionStoreProvider.overrideWithValue(MemorySessionStore()),
        ],
        child: const MaterialApp(home: LoginScreen()),
      ));
      await t.pumpAndSettle();
      await t.tap(find.text('Entrar'));
      await t.pump();
      expect(find.text('Requerido'), findsNWidgets(2));
    });
  });

  group('Errores amigables (Fase C)', () {
    testWidgets('búsqueda muestra mensaje sin ApiException() crudo',
        (t) async {
      final failing = SpeciesRepository(clientWith(FakeAdapter(
          (o) => jsonBody({'error': 'Parámetro q requerido.'}, 400))));
      // Store offline sin platform channels (path_provider no existe en tests).
      await t.pumpWidget(ProviderScope(
        overrides: [
          speciesRepositoryProvider.overrideWithValue(failing),
          offlineStoreProvider.overrideWithValue(AsyncValue.data(
              OfflineStore(db: MemoryOfflineDb(), filesDir: '/tmp'))),
        ],
        // Scaffold como en prod (las pantallas viven en HomeShell).
        child: const MaterialApp(home: Scaffold(body: SpeciesSearchScreen())),
      ));
      await t.enterText(find.byType(TextField), 'x');
      await t.tap(find.text('Buscar'));
      await t.pumpAndSettle();
      expect(find.text('Parámetro q requerido.'), findsOneWidget);
      expect(find.text('Reintentar'), findsOneWidget);
      expect(find.textContaining('ApiException('), findsNothing);
    });
  });

  group('SpeciesRepository (offline-ready)', () {
    test('search propaga ApiException con mensaje limpio', () async {
      final api = clientWith(FakeAdapter(
          (o) => jsonBody({'error': 'Parámetro q requerido.'}, 400)));
      final repo = SpeciesRepository(api);
      try {
        await repo.search(q: 'x');
        fail('debió lanzar');
      } on ApiException catch (e) {
        // La UI muestra e.message (sin nombre de clase).
        expect(e.message, 'Parámetro q requerido.');
      }
    });
  });

  group('Registro con consentimiento (LFPDPPP B2)', () {
    testWidgets('sin checkbox no llama a la red', (t) async {
      var calls = 0;
      final api = clientWith(FakeAdapter((o) {
        calls++;
        return jsonBody({'status': 'created'}, 201);
      }));
      await t.pumpWidget(ProviderScope(
        overrides: [
          sessionStoreProvider.overrideWithValue(MemorySessionStore()),
          apiClientProvider.overrideWithValue(api),
        ],
        child: const MaterialApp(home: LoginScreen()),
      ));
      await t.pumpAndSettle();
      await t.tap(find.text('Crear cuenta nueva'));
      await t.pumpAndSettle();
      await t.enterText(find.byType(TextField).first, 'nuevo9');
      await t.enterText(find.byType(TextField).last, 'Segura123!');
      await t.tap(find.text('Crear cuenta'));
      await t.pump();
      expect(
          find.text(
              'Debes aceptar el uso de datos para crear tu cuenta.'),
          findsOneWidget);
      expect(calls, 0);
    });
  });
}
