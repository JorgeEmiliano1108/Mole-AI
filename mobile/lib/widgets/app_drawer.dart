/// Drawer lateral (issue 15): secciones usuario + admin con RoleGuard.
///
/// hamburger → AppBar leading automático al haber `drawer`. La sección admin
/// solo se renderiza con `isAdmin`; el router además redirige (defensa doble).
library;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import 'package:mole_ai/features/auth/auth_controller.dart';
import 'package:mole_ai/features/alerts/alerts.dart';

class _Entry {
  const _Entry(this.label, this.icon, this.route);
  final String label;
  final IconData icon;
  final String route;
}

const _userEntries = [
  _Entry('Especies', Icons.eco_outlined, '/especies'),
  _Entry('Chat', Icons.chat_outlined, '/chat'),
  _Entry('Mapa', Icons.map_outlined, '/mapa'),
  _Entry('Reportes', Icons.picture_as_pdf_outlined, '/reportes'),
  _Entry('Historial diagnósticos', Icons.history_outlined, '/diagnostico/historial'),
];

const _adminEntries = [
  _Entry('Panel admin', Icons.admin_panel_settings_outlined, '/admin'),
  _Entry('Métricas', Icons.insights_outlined, '/admin/metricas'),
  _Entry('Base conocimiento', Icons.library_books_outlined, '/admin/knowledge'),
  _Entry('Usuarios', Icons.group_outlined, '/admin/usuarios'),
  _Entry('Dispositivos', Icons.router_outlined, '/admin/dispositivos'),
  _Entry('Auditoría', Icons.history_outlined, '/admin/auditoria'),
  _Entry('Centro de fallas', Icons.warning_amber_outlined, '/admin/fallas'),
];

class AppDrawer extends ConsumerWidget {
  const AppDrawer({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final auth = ref.watch(authControllerProvider);
    final loc =
        GoRouterState.of(context).matchedLocation;
    Widget tile(_Entry e) => ListTile(
          leading: Icon(e.icon),
          title: Text(e.label),
          selected: loc == e.route,
          onTap: () {
            Navigator.of(context).pop();
            context.go(e.route);
          },
        );

    return Drawer(
      child: SafeArea(
        child: ListView(
          padding: EdgeInsets.zero,
          children: [
            DrawerHeader(
              decoration: BoxDecoration(
                  color: Theme.of(context).colorScheme.primaryContainer),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                mainAxisAlignment: MainAxisAlignment.end,
                children: [
                  const Text('Mole.AI',
                      style: TextStyle(
                          fontSize: 22, fontWeight: FontWeight.bold)),
                  Text('Rol: ${auth.role ?? 'usuario'}'),
                ],
              ),
            ),
            const Padding(
              padding: EdgeInsets.fromLTRB(16, 8, 16, 4),
              child: Text('MONITOREO'),
            ),
            for (final e in _userEntries) tile(e),
            Consumer(builder: (context, ref, _) {
              final unread = ref.watch(unreadAlertsProvider);
              return ListTile(
                leading: const Icon(Icons.notifications_outlined),
                title: const Text('Mis avisos'),
                trailing: unread > 0 ? Badge.count(count: unread) : null,
                selected: loc == '/avisos',
                onTap: () {
                  Navigator.of(context).pop();
                  context.go('/avisos');
                },
              );
            }),
            if (auth.isAdmin) ...[
              const Divider(),
              const Padding(
                padding: EdgeInsets.fromLTRB(16, 8, 16, 4),
                child: Text('ADMINISTRACIÓN'),
              ),
              for (final e in _adminEntries) tile(e),
            ],
            const Divider(),
            ListTile(
              leading: const Icon(Icons.logout),
              title: const Text('Cerrar sesión'),
              onTap: () {
                Navigator.of(context).pop();
                ref.read(authControllerProvider.notifier).logout();
              },
            ),
          ],
        ),
      ),
    );
  }
}
