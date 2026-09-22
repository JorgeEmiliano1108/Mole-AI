/// Mole.AI móvil — 7 historias + offline real.
///
/// Observabilidad B6: `runZonedGuarded` captura errores async no manejados;
/// Sentry (paquete Dart puro; sin bindings nativos porque `sentry_flutter`
/// 8.x fija `languageVersion 1.6`, incompatible con Kotlin 2.2 del proyecto)
/// solo si `--dart-define=SENTRY_DSN=...` (sin DSN = no-op).
/// Nunca se registran tokens ni PII (ver `core/errors.dart`: solo mensajes).
library;

import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:sentry/sentry.dart';

import 'package:mole_ai/core/app_router.dart';
import 'package:mole_ai/core/notify.dart';

const _sentryDsn = String.fromEnvironment('SENTRY_DSN', defaultValue: '');

Future<void> main() async {
  runZonedGuarded(() async {
    WidgetsFlutterBinding.ensureInitialized();
    await NotifyService.init();
    if (_sentryDsn.isNotEmpty) {
      await Sentry.init(
        (o) {
          o.dsn = _sentryDsn;
          o.sendDefaultPii = false;
          o.tracesSampleRate = 0.1;
        },
      );
    }
    runApp(const ProviderScope(child: MoleApp()));
  }, (error, stack) async {
    debugPrint('uncaught: $error');
    if (_sentryDsn.isNotEmpty) {
      await Sentry.captureException(error, stackTrace: stack);
    }
  });
}

class MoleApp extends ConsumerWidget {
  const MoleApp({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final router = buildRouter(ref);
    return MaterialApp.router(
      title: 'Mole.AI',
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.green),
        useMaterial3: true,
      ),
      darkTheme: ThemeData(
        colorScheme: ColorScheme.fromSeed(
            seedColor: Colors.green, brightness: Brightness.dark),
        useMaterial3: true,
      ),
      routerConfig: router,
    );
  }
}
