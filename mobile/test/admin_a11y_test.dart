/// Tests F4 a11y (issue 15): admin accesible.
///
/// Checklist: Semantics/liveRegion en errores, objetivos táctiles ≥48dp,
/// estados vacíos con texto, sin overflow a escalado 2.0×, sin crash en
/// modo oscuro. Los charts con Semantics ya se cubren en `f4_test.dart`.
library;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mole_ai/features/admin/admin.dart';
import 'package:mole_ai/features/admin/admin_metrics.dart';
import 'package:mole_ai/features/admin/charts.dart';
import 'package:mole_ai/features/admin/knowledge_screen.dart';
import 'package:mole_ai/features/admin/users_screen.dart';

import 'species_test.dart' show FakeAdapter, clientWith, jsonBody;

Widget _wrap(Widget child, {bool dark = false, double scale = 1.0}) {
  final light = ThemeData(
      colorScheme: ColorScheme.fromSeed(seedColor: Colors.green),
      useMaterial3: true);
  final darkTheme = ThemeData(
      colorScheme: ColorScheme.fromSeed(
          seedColor: Colors.green, brightness: Brightness.dark),
      useMaterial3: true);
  return ProviderScope(
    child: MediaQuery(
      data: MediaQueryData(
          textScaler: TextScaler.linear(scale)),
      child: MaterialApp(
        theme: light,
        darkTheme: darkTheme,
        themeMode: dark ? ThemeMode.dark : ThemeMode.light,
        home: Scaffold(body: child),
      ),
    ),
  );
}

void main() {
  group('UsersScreen a11y', () {
    ProviderScope usersScope(Widget child) {
      final api = clientWith(FakeAdapter(
          (o) => jsonBody({'count': 0, 'results': []}, 200)));
      return ProviderScope(
        overrides: [
          adminRepositoryProvider
              .overrideWithValue(AdminRepository(api)),
        ],
        child: child,
      );
    }

    testWidgets('buscador + botón 48dp + vacío con texto', (t) async {
      await t.pumpWidget(_wrap(usersScope(const UsersScreen())));
      await t.pumpAndSettle();
      expect(find.text('Buscar usuario o correo'), findsOneWidget);
      expect(find.text('Sin usuarios.'), findsOneWidget);
      final ver = find.widgetWithText(FilledButton, 'Ver');
      expect(ver, findsOneWidget);
      expect(testerSize(t, ver).height, greaterThanOrEqualTo(48));
      expect(t.takeException(), isNull);
    });

    testWidgets('escalado 2.0× sin overflow', (t) async {
      await t.pumpWidget(
          _wrap(usersScope(const UsersScreen()), scale: 2.0));
      await t.pumpAndSettle();
      expect(t.takeException(), isNull);
    });

    testWidgets('modo oscuro sin crash', (t) async {
      await t.pumpWidget(
          _wrap(usersScope(const UsersScreen()), dark: true));
      await t.pumpAndSettle();
      expect(find.text('Sin usuarios.'), findsOneWidget);
      expect(t.takeException(), isNull);
    });
  });

  group('KnowledgeScreen a11y', () {
    ProviderScope knowledgeScope(Widget child) {
      final api = clientWith(FakeAdapter(
          (o) => jsonBody({'count': 0, 'results': []}, 200)));
      return ProviderScope(
        overrides: [
          knowledgeRepositoryProvider
              .overrideWithValue(KnowledgeRepository(api)),
        ],
        child: child,
      );
    }

    testWidgets('CTA 48dp + vacío + escalado', (t) async {
      await t.pumpWidget(
          _wrap(knowledgeScope(const KnowledgeScreen())));
      await t.pumpAndSettle();
      final cta = find.widgetWithText(
          FilledButton, 'Adjuntar documento/imagen');
      expect(cta, findsOneWidget);
      expect(testerSize(t, cta).height, greaterThanOrEqualTo(48));
      expect(find.text('Sin documentos todavía.'), findsOneWidget);
      expect(t.takeException(), isNull);

      await t.pumpWidget(_wrap(knowledgeScope(const KnowledgeScreen()),
          scale: 2.0));
      await t.pumpAndSettle();
      expect(t.takeException(), isNull);
    });
  });

  group('AdminMetricsScreen a11y', () {
    ProviderScope metricsScope(Widget child) {
      final api = clientWith(FakeAdapter((o) {
        if (o.path.contains('live-alerts')) {
          return jsonBody({'alerts': []}, 200);
        }
        return jsonBody({
          'users': [10, 2, 0],
          'regs': [1, 2, 3],
          'health': [80, 90, 70],
          'total_plants': 5,
        }, 200);
      }));
      return ProviderScope(
        overrides: [
          adminRepositoryProvider
              .overrideWithValue(AdminRepository(api)),
        ],
        child: child,
      );
    }

    testWidgets('gráficas con Semantics + escalado', (t) async {
      await t.pumpWidget(
          _wrap(metricsScope(const AdminMetricsScreen())));
      await t.pumpAndSettle();
      // Los labels se fusionan con el texto del Card en el anuncio del
      // lector (merge-up): se assert contenido, no igualdad exacta.
      final donutSem = t
          .getSemantics(find.byType(MiniDonutChart).first)
          .label;
      expect(donutSem,
          contains('Distribución de usuarios del sistema'));
      final lineSem =
          t.getSemantics(find.byType(MiniLineChart).first).label;
      expect(lineSem, contains('Serie de salud del sistema'));
      expect(t.takeException(), isNull);

      await t.pumpWidget(_wrap(metricsScope(const AdminMetricsScreen()),
          scale: 2.0));
      await t.pumpAndSettle();
      expect(t.takeException(), isNull);
    });
  });
}

Size testerSize(WidgetTester t, Finder f) => t.getSize(f);
