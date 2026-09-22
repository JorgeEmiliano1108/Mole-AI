/// Tests F4 (issue 15): roles, admin repos, gráficas, detalle e historial.
library;

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mole_ai/features/admin/admin.dart';
import 'package:mole_ai/features/admin/charts.dart';
import 'package:mole_ai/features/auth/auth_controller.dart';
import 'package:mole_ai/features/plants/plants.dart';
import 'package:mole_ai/features/vision/vision.dart';

import 'species_test.dart' show FakeAdapter, clientWith, jsonBody;

void main() {
  group('AuthState.isAdmin (RoleGuard)', () {
    test('admin y superuser sí; user y null no', () {
      expect(
          const AuthState(
                  status: AuthStatus.authenticated, role: 'admin')
              .isAdmin,
          isTrue);
      expect(
          const AuthState(
                  status: AuthStatus.authenticated, role: 'superuser')
              .isAdmin,
          isTrue);
      expect(
          const AuthState(
                  status: AuthStatus.authenticated, role: 'user')
              .isAdmin,
          isFalse);
      expect(
          const AuthState(status: AuthStatus.authenticated).isAdmin,
          isFalse);
    });
  });

  group('AdminRepository (contrato §6b)', () {
    test('statistics mapea users/regs/health/total', () async {
      final api = clientWith(FakeAdapter((o) => jsonBody({
            'users': [10, 2, 0],
            'regs': [1, 2, 3],
            'health': [80, 90, 70],
            'total_plants': 5,
          }, 200)));
      final m = await AdminRepository(api).statistics();
      expect(m.totalPlants, 5);
      expect(m.health, hasLength(3));
    });

    test('updateUser usa PATCH con rol', () async {
      String? method;
      Object? sent;
      final api = clientWith(FakeAdapter((o) {
        method = o.method;
        sent = o.data;
        return jsonBody({'role': 'Admin', 'is_active': true}, 200);
      }));
      final u = await AdminRepository(api)
          .updateUser(7, role: 'Admin');
      expect(method, 'PATCH');
      expect((sent as Map)['role'], 'Admin');
      expect(u.username, isNotEmpty);
    });

    test('knowledge request/confirm', () async {
      final api = clientWith(FakeAdapter((o) {
        if (o.path.endsWith('upload/request/')) {
          return jsonBody({
            'presigned_url': 'http://minio/x',
            's3_key': 'k',
            'record_id': 'r1',
            'expires_in': 900
          }, 201);
        }
        return jsonBody(
            {'record_id': 'r1', 'status': 'UPLOADED', 'file_size': 10},
            200);
      }));
      final repo = KnowledgeRepository(api);
      final req = await repo.requestUpload('documents',
          filename: 'a.pdf', contentType: 'application/pdf', fileSize: 10);
      expect(req['record_id'], 'r1');
      final done =
          await repo.confirm('r1', 'document');
      expect(done.status, 'UPLOADED');
    });
  });

  group('charts (sin dependencias)', () {
    test('normalize vacía/plana/rango', () {
      expect(normalize([]), isEmpty);
      expect(normalize([5, 5, 5]), [0.5, 0.5, 0.5]);
      expect(normalize([0.0, 5.0, 10.0]), [0.0, 0.5, 1.0]);
    });

    testWidgets('MiniLineChart renderiza con Semantics', (t) async {
      await t.pumpWidget(const MaterialApp(
          home: Scaffold(
              body: MiniLineChart(
                  values: [1, 2, 3], semanticLabel: 'Serie prueba'))));
      expect(find.bySemanticsLabel('Serie prueba'), findsOneWidget);
    });

    testWidgets('MiniBarChart + MiniDonutChart renderizan', (t) async {
      await t.pumpWidget(MaterialApp(
          home: Scaffold(
              body: Column(children: const [
        MiniBarChart(values: [1, 2], semanticLabel: 'Barras prueba'),
        MiniDonutChart(
            fractions: [0.7, 0.3], semanticLabel: 'Dona prueba'),
      ]))));
      expect(find.bySemanticsLabel('Barras prueba'), findsOneWidget);
      expect(find.bySemanticsLabel('Dona prueba'), findsOneWidget);
    });
  });

  group('Detalle e historial (repos existentes)', () {
    test('plant detail parsea', () async {
      final api = clientWith(FakeAdapter((o) => jsonBody({
            'id': 'p1',
            'nickname': 'Jito',
            'species_id': null,
            'created_at': '2026-01-01'
          }, 200)));
      final p = await PlantsRepository(api).detail('p1');
      expect(p.nickname, 'Jito');
    });

    test('vision history lista', () async {
      final api = clientWith(FakeAdapter((o) => jsonBody({
            'results': [
              {'condition': 'sana', 'analyzed_at': '2026-01-02'}
            ]
          }, 200)));
      final h = await VisionRepository(api).history();
      expect(h.single['condition'], 'sana');
    });
  });
}
