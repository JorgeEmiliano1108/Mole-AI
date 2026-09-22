/// Panel admin + Métricas (issue 15, rol admin|superuser).
///
/// Métricas: `GET admin/statistics` + `live-alerts`, dibujadas con gráficas
/// propias (`charts.dart`, sin dependencias). Acceso doble-gateado:
/// `RoleGuard` en router + `isAdmin` en drawer.
library;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import 'package:mole_ai/core/errors.dart';
import 'package:mole_ai/features/admin/admin.dart';
import 'package:mole_ai/features/admin/charts.dart';
import 'package:mole_ai/features/auth/auth_controller.dart';

final adminRepositoryProvider = Provider<AdminRepository>(
    (ref) => AdminRepository(ref.watch(apiClientProvider)));

String _friendly(Object e) => e is ApiException
    ? e.message
    : 'Error inesperado. Intenta de nuevo.';

class AdminPanelScreen extends StatelessWidget {
  const AdminPanelScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return SafeArea(
      child: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          Card(
            child: ListTile(
              leading: const Icon(Icons.insights_outlined),
              title: const Text('Métricas del sistema'),
              subtitle:
                  const Text('Usuarios, registros, salud, alertas'),
              trailing: const Icon(Icons.chevron_right),
              onTap: () => context.go('/admin/metricas'),
            ),
          ),
          Card(
            child: ListTile(
              leading: const Icon(Icons.library_books_outlined),
              title: const Text('Base de conocimiento'),
              subtitle: const Text('Adjuntar documentos e imágenes RAG'),
              trailing: const Icon(Icons.chevron_right),
              onTap: () => context.go('/admin/knowledge'),
            ),
          ),
          Card(
            child: ListTile(
              leading: const Icon(Icons.group_outlined),
              title: const Text('Usuarios'),
              subtitle: const Text('Roles y estado de cuentas'),
              trailing: const Icon(Icons.chevron_right),
              onTap: () => context.go('/admin/usuarios'),
            ),
          ),
        ],
      ),
    );
  }
}

class AdminMetricsScreen extends ConsumerStatefulWidget {
  const AdminMetricsScreen({super.key});

  @override
  ConsumerState<AdminMetricsScreen> createState() =>
      _AdminMetricsScreenState();
}

class _AdminMetricsScreenState extends ConsumerState<AdminMetricsScreen> {
  SystemMetrics? _metrics;
  List<Map<String, dynamic>> _alerts = [];
  bool _loading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    Future.microtask(_load);
  }

  Future<void> _load() async {
    try {
      final repo = ref.read(adminRepositoryProvider);
      final m = await repo.statistics();
      final a = await repo.liveAlerts();
      if (mounted) {
        setState(() {
          _metrics = m;
          _alerts = a;
          _loading = false;
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _error = _friendly(e);
          _loading = false;
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_loading) return const Center(child: CircularProgressIndicator());
    if (_error != null) {
      return Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Semantics(
              liveRegion: true,
              child: Text(_error!,
                  style: TextStyle(
                      color: Theme.of(context).colorScheme.error)),
            ),
            const SizedBox(height: 12),
            OutlinedButton(onPressed: _load, child: const Text('Reintentar')),
          ],
        ),
      );
    }
    final m = _metrics!;
    final totalUsers =
        m.users.fold<int>(0, (a, b) => a + b).clamp(1, 1 << 31);
    return RefreshIndicator(
      onRefresh: _load,
      child: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          Card(
            child: Padding(
              padding: const EdgeInsets.all(12),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('${m.totalPlants} plantas registradas',
                      style: Theme.of(context).textTheme.titleMedium),
                  const SizedBox(height: 8),
                  MiniDonutChart(
                    fractions: m.users.map((u) => u.toDouble()).toList(),
                    semanticLabel:
                        'Distribución de usuarios del sistema',
                  ),
                ],
              ),
            ),
          ),
          Card(
            child: Padding(
              padding: const EdgeInsets.all(12),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text('Registros (7 días)'),
                  MiniBarChart(
                      values: m.registrations,
                      semanticLabel: 'Registros por día'),
                ],
              ),
            ),
          ),
          Card(
            child: Padding(
              padding: const EdgeInsets.all(12),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text('Salud del sistema'),
                  MiniLineChart(
                      values: m.health,
                      semanticLabel: 'Serie de salud del sistema'),
                ],
              ),
            ),
          ),
          Card(
            child: Padding(
              padding: const EdgeInsets.all(12),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('Alertas (${_alerts.length})',
                      style:
                          Theme.of(context).textTheme.titleMedium),
                  for (final a in _alerts.take(5))
                    ListTile(
                      dense: true,
                      leading: Icon(
                          a['tipo'] == 'error'
                              ? Icons.error_outline
                              : Icons.warning_amber_outlined,
                          color: a['tipo'] == 'error'
                              ? Theme.of(context).colorScheme.error
                              : null),
                      title: Text('${a['msg'] ?? ''}'),
                    ),
                  if (_alerts.isEmpty)
                    const Text('Sin alertas. Sistema estable.'),
                ],
              ),
            ),
          ),
          Text('Usuarios totales: $totalUsers',
              style: Theme.of(context).textTheme.bodySmall),
        ],
      ),
    );
  }
}
