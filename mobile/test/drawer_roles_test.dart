/// Tests F4 (issue 15): drawer lateral por rol + navegación admin.
///
/// Criterio issue 15: "Drawer por rol testeado (admin ve sección, user no)".
/// Se bombea el [AppDrawer] real bajo un GoRouter mínimo (el drawer lee
/// `GoRouterState.of`, `app_drawer.dart:41-42`) con el [AuthController]
/// fijado por rol. Sin red: FakeAdapter + MemorySessionStore.
library;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:go_router/go_router.dart';
import 'package:mole_ai/core/session_store.dart';
import 'package:mole_ai/features/auth/auth_controller.dart';
import 'package:mole_ai/widgets/app_drawer.dart';

import 'species_test.dart' show FakeAdapter, clientWith, jsonBody;

/// Sesión fija por rol: sin restore de red ni timers de refresh.
class FakeAuthController extends AuthController {
  FakeAuthController(this._fixed);
  final AuthState _fixed;
  @override
  AuthState build() => _fixed;
}

/// Rutas del drawer + base con llave para abrir el drawer en tests.
({GoRouter router, GlobalKey<ScaffoldState> key}) stubShell() {
  final key = GlobalKey<ScaffoldState>();
  const drawerRoutes = [
    '/especies',
    '/chat',
    '/mapa',
    '/reportes',
    '/diagnostico/historial',
    '/admin',
    '/admin/metricas',
    '/admin/knowledge',
    '/admin/usuarios',
  ];
  final router = GoRouter(
    initialLocation: '/',
    routes: [
      GoRoute(
        path: '/',
        builder: (context, state) => Scaffold(
          key: key,
          drawer: const AppDrawer(),
          body: const Text('base'),
        ),
      ),
      for (final r in drawerRoutes)
        GoRoute(
          path: r,
          builder: (context, state) => Scaffold(body: Text('destino:$r')),
        ),
    ],
  );
  return (router: router, key: key);
}

Future<void> pumpDrawer(
  WidgetTester t,
  AuthState auth,
  GlobalKey<ScaffoldState> key,
  GoRouter router,
) async {
  // Viewport alto: todo el drawer cabe sin scroll (el scroll colapsa
  // el header del árbol en este SDK; ver diagnóstico F4).
  t.view.physicalSize = const Size(800, 2000);
  t.view.devicePixelRatio = 1.0;
  addTearDown(t.view.resetPhysicalSize);
  final session = MemorySessionStore()
    ..token = 'T'
    ..role = auth.role ?? 'user';
  final api = clientWith(
    FakeAdapter((o) => jsonBody(<String, dynamic>{}, 200)),
    session: session,
  );
  await t.pumpWidget(ProviderScope(
    overrides: [
      sessionStoreProvider.overrideWithValue(session),
      apiClientProvider.overrideWithValue(api),
      authControllerProvider.overrideWith(() => FakeAuthController(auth)),
    ],
    child: MaterialApp.router(routerConfig: router),
  ));
  await t.pumpAndSettle();
  key.currentState!.openDrawer();
  await t.pumpAndSettle();
}

void main() {
  group('AppDrawer por rol (issue 15)', () {
    testWidgets('admin ve la sección ADMINISTRACIÓN', (t) async {
      final shell = stubShell();
      await pumpDrawer(
        t,
        const AuthState(
            status: AuthStatus.authenticated, role: 'admin'),
        shell.key,
        shell.router

      );
      expect(find.text('ADMINISTRACIÓN'), findsOneWidget);
      expect(find.text('Panel admin'), findsOneWidget);
      expect(find.text('Métricas'), findsOneWidget);
      expect(find.text('Base conocimiento'), findsOneWidget);
      expect(find.text('Usuarios'), findsOneWidget);
      expect(find.text('Rol: admin'), findsOneWidget);
      expect(t.takeException(), isNull);
    });

    testWidgets('superuser también ve la sección admin', (t) async {
      final shell = stubShell();
      await pumpDrawer(
        t,
        const AuthState(
            status: AuthStatus.authenticated, role: 'superuser'),
        shell.key,
        shell.router

      );
      expect(find.text('ADMINISTRACIÓN'), findsOneWidget);
      expect(find.text('Usuarios'), findsOneWidget);
    });

    testWidgets('user botánico NO ve la sección admin', (t) async {
      final shell = stubShell();
      await pumpDrawer(
        t,
        const AuthState(
            status: AuthStatus.authenticated, role: 'user'),
        shell.key,
        shell.router,
      );
      expect(find.text('ADMINISTRACIÓN'), findsNothing);
      expect(find.text('Panel admin'), findsNothing);
      expect(find.text('Usuarios'), findsNothing);
      // Secciones de monitoreo sí visibles para todos.
      expect(find.text('Especies'), findsOneWidget);
      expect(find.text('Chat'), findsOneWidget);
      expect(find.text('Mapa'), findsOneWidget);
      expect(find.text('Reportes'), findsOneWidget);
      expect(find.text('Historial diagnósticos'), findsOneWidget);
      expect(t.takeException(), isNull);
    });

    testWidgets('tap en Métricas navega a /admin/metricas', (t) async {
      final shell = stubShell();
      await pumpDrawer(
        t,
        const AuthState(
            status: AuthStatus.authenticated, role: 'admin'),
        shell.key,
        shell.router

      );
      await t.tap(find.text('Métricas'));
      await t.pumpAndSettle();
      expect(find.text('destino:/admin/metricas'), findsOneWidget);
      expect(t.takeException(), isNull);
    });
  });
}
