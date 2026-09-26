/// Tests N-2: portal admin (fallas, dispositivos, auditoría + gate de rol).
library;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:dio/dio.dart';
import 'package:go_router/go_router.dart';
import 'package:mole_ai/features/admin/audit_screen.dart';
import 'package:mole_ai/features/admin/devices_screen.dart';
import 'package:mole_ai/features/admin/system_events_screen.dart';
import 'package:mole_ai/features/auth/auth_controller.dart';

import 'drawer_roles_test.dart' show FakeAuthController;
import 'species_test.dart' show FakeAdapter, clientWith, jsonBody;

const _eventsPayload = {
  'security': [
    {'tipo': 'warn', 'action': 'ADMIN_UPDATE_USER', 'user_id': 7, 'timestamp': 't1'}
  ],
  'devices': [
    {'tipo': 'error', 'msg': "Nodo 'n1' en estado offline", 'device_id': 'd1', 'last_seen': null}
  ],
  'telemetry': [
    {'tipo': 'warn', 'msg': 'Humedad baja (30%)', 'source': 'soil', 'recorded_at': 't2'}
  ],
  'services': [
    {'tipo': 'error', 'service': 'ms3_reports', 'status': 'down', 'msg': 'x'}
  ],
};

const _devicesPayload = {
  'results': [
    {'id': 'd1', 'name': 'nodo-uno', 'status': 'warning', 'last_seen': null, 'owner': 'ana'}
  ]
};

const _auditPayload = {
  'results': [
    {'id': 1, 'action': 'ADMIN_UPDATE_USER', 'user_id': 7, 'ip_address': '9.9.9.9',
     'details': 'Actualizado user_id=7.', 'timestamp': 't3'}
  ],
  'page': 1, 'num_pages': 1, 'count': 1,
};

ResponseBody _route(RequestOptions o) {
  final p = o.path;
  if (p.contains('admin/system-events')) return jsonBody(_eventsPayload, 200);
  if (p.contains('admin/devices')) return jsonBody(_devicesPayload, 200);
  if (p.contains('admin/audit-log')) return jsonBody(_auditPayload, 200);
  return jsonBody({}, 200);
}

ProviderScope _scope(Widget child, AuthState auth) => ProviderScope(
      overrides: [
        apiClientProvider.overrideWithValue(clientWith(FakeAdapter(_route))),
        authControllerProvider.overrideWith(() => FakeAuthController(auth)),
      ],
      child: MaterialApp(home: Scaffold(body: child)),
    );

const _adminAuth = AuthState(status: AuthStatus.authenticated, role: 'admin');

void main() {
  group('Portal admin (issue N-2)', () {
    testWidgets('Centro de fallas renderiza 4 secciones', (t) async {
      await t.pumpWidget(_scope(const SystemEventsScreen(), _adminAuth));
      await t.pump();
      await t.pump(const Duration(milliseconds: 100));
      for (final s in ['Seguridad', 'Dispositivos', 'Telemetría', 'Servicios']) {
        expect(find.text(s), findsOneWidget);
      }
      expect(find.textContaining("Nodo 'n1'"), findsOneWidget);
      expect(find.textContaining('ms3_reports'), findsOneWidget);
      final lab =
          t.getSemantics(find.textContaining("Nodo 'n1'")).label;
      expect(lab, contains("error: Nodo 'n1' en estado offline"));
      expect(lab, contains('Sin contacto registrado'));
    });

    testWidgets('Dispositivos lista flota sin tokens', (t) async {
      await t.pumpWidget(_scope(const DevicesScreen(), _adminAuth));
      await t.pump();
      await t.pump(const Duration(milliseconds: 100));
      expect(find.text('nodo-uno'), findsOneWidget);
      expect(find.textContaining('Dueño: ana'), findsOneWidget);
      final dlab = t.getSemantics(find.text('nodo-uno')).label;
      expect(dlab, contains('nodo-uno, estado warning, dueño ana'));
    });

    testWidgets('Auditoría lista y filtra', (t) async {
      await t.pumpWidget(_scope(const AuditScreen(), _adminAuth));
      await t.pump();
      await t.pump(const Duration(milliseconds: 100));
      expect(find.text('ADMIN_UPDATE_USER'), findsOneWidget);
      expect(find.text('1 registro(s)'), findsOneWidget);
      final alab = t.getSemantics(find.text('ADMIN_UPDATE_USER')).label;
      expect(alab, contains('ADMIN_UPDATE_USER, usuario 7, t3'));
    });

    testWidgets('botánico con URL directa al portal es redirigido', (t) async {
      final router = GoRouter(
        initialLocation: '/admin/fallas',
        redirect: (context, state) {
          final loc = state.matchedLocation;
          if (loc.startsWith('/admin')) return '/inicio';
          return null;
        },
        routes: [
          GoRoute(path: '/inicio', builder: (context, state) => const Text('INICIO')),
          GoRoute(
              path: '/admin/fallas',
              builder: (context, state) => const SystemEventsScreen()),
        ],
      );
      await t.pumpWidget(ProviderScope(
        overrides: [
          apiClientProvider.overrideWithValue(clientWith(FakeAdapter(_route))),
          authControllerProvider.overrideWith(() => FakeAuthController(
              const AuthState(status: AuthStatus.authenticated, role: 'user'))),
        ],
        child: MaterialApp.router(routerConfig: router),
      ));
      await t.pump();
      await t.pump(const Duration(milliseconds: 100));
      expect(find.text('INICIO'), findsOneWidget);
      expect(find.text('Centro de fallas'), findsNothing);
    });
  });
}
