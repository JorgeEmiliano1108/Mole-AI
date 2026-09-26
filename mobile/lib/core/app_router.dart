/// Router de la app (issue 14): shell pública vs autenticada + roles.
///
/// - Sin sesión: portal público (`/inicio-publico`), especies públicas,
///   login/registro/consentimiento, forgot-password. Nada exige token.
/// - Con sesión: `/inicio` (HomeShell actual). `isAdmin` funda la sección
///   admin de F4 (drawer + `RoleGuard`); hoy redirige igual que user.
/// Deep-links listos: `/especies`, `/plantas/:id` (F4), `/diagnostico`.
library;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import 'package:mole_ai/features/admin/admin_metrics.dart';
import 'package:mole_ai/features/admin/audit_screen.dart';
import 'package:mole_ai/features/admin/devices_screen.dart';
import 'package:mole_ai/features/admin/knowledge_screen.dart';
import 'package:mole_ai/features/admin/system_events_screen.dart';
import 'package:mole_ai/features/admin/users_screen.dart';
import 'package:mole_ai/features/alerts/alerts_screen.dart';
import 'package:mole_ai/features/auth/auth_controller.dart';
import 'package:mole_ai/features/auth/auth_screens.dart';
import 'package:mole_ai/features/auth/forgot_password.dart';
import 'package:mole_ai/features/chat/chat_screen.dart';
import 'package:mole_ai/features/map/map_screen.dart';
import 'package:mole_ai/features/plants/plant_detail.dart';
import 'package:mole_ai/features/public/public_home.dart';
import 'package:mole_ai/features/reports/reports_screen.dart';
import 'package:mole_ai/features/species/species_search_screen.dart';
import 'package:mole_ai/features/vision/diagnosis_history.dart';
import 'package:mole_ai/features/weather/weather_screen.dart';
import 'package:mole_ai/home_shell.dart';

/// Rutas públicas (sin token).
const _publicPaths = {
  '/inicio-publico',
  '/especies-publico',
  '/login',
  '/registro',
  '/consentimiento',
  '/recuperar',
  '/recuperar/confirmar',
};

GoRouter buildRouter(WidgetRef ref) {
  return GoRouter(
    initialLocation: '/inicio-publico',
    refreshListenable: _AuthRefresh(ref),
    redirect: (context, state) {
      final auth = ref.read(authControllerProvider);
      final loc = state.matchedLocation;
      final isPublic = _publicPaths.contains(loc) ||
          loc.startsWith('/especies-publico');
      switch (auth.status) {
        case AuthStatus.loading:
          return null; // splash gestionado por MoleApp
        case AuthStatus.unauthenticated:
          return isPublic ? null : '/inicio-publico';
        case AuthStatus.needsConsent:
          return loc == '/consentimiento' ? null : '/consentimiento';
        case AuthStatus.authenticated:
          // Fundamento F4: gate admin por rol (hoy mismo destino).
          if (loc.startsWith('/admin') && !auth.isAdmin) return '/inicio';
          return isPublic &&
                  loc != '/especies-publico' &&
                  loc != '/inicio-publico'
              ? '/inicio'
              : null;
      }
    },
    routes: [
      GoRoute(
        path: '/inicio-publico',
        builder: (context, state) => const PublicHomeScreen(),
      ),
      GoRoute(
        path: '/especies-publico',
        builder: (context, state) => const SpeciesSearchScreen(publicMode: true),
      ),
      GoRoute(
        path: '/login',
        builder: (context, state) => const LoginScreen(),
      ),
      GoRoute(
        path: '/registro',
        builder: (context, state) => const LoginScreen(registerMode: true),
      ),
      GoRoute(
        path: '/consentimiento',
        builder: (context, state) => const ConsentScreen(),
      ),
      GoRoute(
        path: '/recuperar',
        builder: (context, state) => const ForgotRequestScreen(),
      ),
      GoRoute(
        path: '/recuperar/confirmar',
        builder: (context, state) => ForgotConfirmScreen(
          token: state.uri.queryParameters['token'],
        ),
      ),
      GoRoute(
        path: '/inicio',
        builder: (context, state) => const HomeShell(),
      ),
      GoRoute(
        path: '/especies',
        builder: (context, state) => const SpeciesSearchScreen(),
      ),
      GoRoute(
        path: '/plantas/:id',
        builder: (context, state) => PlantDetailScreen(
          plantId: state.pathParameters['id'] ?? '',
        ),
      ),
      GoRoute(
        path: '/clima',
        builder: (context, state) => const WeatherScreen(),
      ),
      GoRoute(
        path: '/chat',
        builder: (context, state) => const ChatScreen(),
      ),
      GoRoute(
        path: '/avisos',
        builder: (context, state) => const AlertsScreen(),
      ),
      GoRoute(
        path: '/mapa',
        builder: (context, state) => const MapScreen(),
      ),
      GoRoute(
        path: '/reportes',
        builder: (context, state) => const ReportsScreen(),
      ),
      GoRoute(
        path: '/diagnostico/historial',
        builder: (context, state) => const DiagnosisHistoryScreen(),
      ),
      GoRoute(
        path: '/admin',
        builder: (context, state) => const AdminPanelScreen(),
      ),
      GoRoute(
        path: '/admin/metricas',
        builder: (context, state) => const AdminMetricsScreen(),
      ),
      GoRoute(
        path: '/admin/knowledge',
        builder: (context, state) => const KnowledgeScreen(),
      ),
      GoRoute(
        path: '/admin/usuarios',
        builder: (context, state) => const UsersScreen(),
      ),
      GoRoute(
        path: '/admin/dispositivos',
        builder: (context, state) => const DevicesScreen(),
      ),
      GoRoute(
        path: '/admin/auditoria',
        builder: (context, state) => const AuditScreen(),
      ),
      GoRoute(
        path: '/admin/fallas',
        builder: (context, state) => const SystemEventsScreen(),
      ),
    ],
  );
}

/// Puente Riverpod→Listenable para `refreshListenable` de go_router.
class _AuthRefresh extends ChangeNotifier {
  _AuthRefresh(this._ref) {
    _ref.listen(authControllerProvider, (_, _) => notifyListeners());
  }
  final WidgetRef _ref;
}
