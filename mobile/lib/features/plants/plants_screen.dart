/// Mis plantas + última telemetría (contrato §3, §4).
///
/// Contenido (sin Scaffold): el [HomeShell] provee AppBar.
library;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:mole_ai/core/errors.dart';
import 'package:mole_ai/core/offline_store.dart';
import 'package:mole_ai/features/auth/auth_controller.dart';
import 'package:mole_ai/features/plants/plants.dart';

final plantsRepositoryProvider = Provider<PlantsRepository>(
    (ref) => PlantsRepository(ref.watch(apiClientProvider)));
final telemetryRepositoryProvider = Provider<TelemetryRepository>(
    (ref) => TelemetryRepository(ref.watch(apiClientProvider)));

String _fmt(double? v, String unit) =>
    v == null ? '—' : '${v.toStringAsFixed(1)} $unit';

String _friendly(Object e) => e is ApiException
    ? e.message
    : 'Error inesperado. Intenta de nuevo.';

class PlantsScreen extends ConsumerStatefulWidget {
  const PlantsScreen({super.key});

  @override
  ConsumerState<PlantsScreen> createState() => _PlantsScreenState();
}

class _PlantsScreenState extends ConsumerState<PlantsScreen> {
  List<Plant> _plants = [];
  final _telemetry = <String, Telemetry>{};
  bool _loading = true;
  bool _offline = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    Future.microtask(_load);
  }

  Future<void> _load() async {
    if (mounted) {
      setState(() {
        _loading = true;
        _error = null;
      });
    }
    try {
      final store = await ref.read(offlineStoreProvider.future);
      final col = await ref
          .read(plantsRepositoryProvider)
          .myCollectionCached(store);
      final plants = col.plants;
      var offline = col.offline;
      final teleRepo = ref.read(telemetryRepositoryProvider);
      final tele = <String, Telemetry>{};
      for (final p in plants) {
        try {
          final r = await teleRepo.latestCached(store, p.id);
          if (r.telemetry != null) tele[p.id] = r.telemetry!;
          offline = offline || r.offline;
        } catch (_) {
          // 404 sin logs: la planta queda sin dato (UI muestra "sin datos").
        }
      }
      if (mounted) {
        setState(() {
          _plants = plants;
          _telemetry.addAll(tele);
          _offline = offline;
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
    if (_loading) {
      return const Center(child: CircularProgressIndicator());
    }
    if (_error != null) {
      return Center(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Semantics(
                liveRegion: true,
                child: Text(_error!,
                    textAlign: TextAlign.center,
                    style: TextStyle(
                        color: Theme.of(context).colorScheme.error)),
              ),
              const SizedBox(height: 12),
              OutlinedButton(
                  onPressed: _load, child: const Text('Reintentar')),
            ],
          ),
        ),
      );
    }
    if (_plants.isEmpty) {
      return const Center(
          child: Text('Sin plantas. Regístralas en la web.'));
    }
    return RefreshIndicator(
      onRefresh: _load,
      child: Column(
        children: [
          if (_offline)
            const Padding(
              padding: EdgeInsets.fromLTRB(12, 12, 12, 0),
              child: Chip(
                avatar: Icon(Icons.cloud_off, size: 18),
                label: Text('Sin conexión: últimos datos conocidos'),
              ),
            ),
          Expanded(
            child: ListView.builder(
              padding: const EdgeInsets.all(12),
              itemCount: _plants.length,
              itemBuilder: (context, i) {
                final p = _plants[i];
                final t = _telemetry[p.id];
                return Card(
                  child: ListTile(
                    title: Text(
                        p.nickname.isEmpty ? '(sin nombre)' : p.nickname),
                    subtitle: t == null || !t.hasData
                        ? const Text('Sin datos (nodo sin logs)')
                        : Text(
                            'Suelo ${_fmt(t.soilHumidity, '%')} · '
                            'Aire ${_fmt(t.airTemperature, '°C')} · '
                            'pH ${_fmt(t.phLevel, '')}'
                            '${t.recordedAt != null ? '\n${_date(t.recordedAt!)}' : ''}'),
                    trailing: const Icon(Icons.chevron_right),
                    onTap: () => context.go('/plantas/${p.id}'),
                  ),
                );
              },
            ),
          ),
        ],
      ),
    );
  }

  /// `2026-09-17T10:00:00Z` → `17/09 10:00` (legible, sin ISO crudo).
  static String _date(String iso) {
    try {
      final d = DateTime.parse(iso).toLocal();
      final mm = d.month.toString().padLeft(2, '0');
      final dd = d.day.toString().padLeft(2, '0');
      final hh = d.hour.toString().padLeft(2, '0');
      final mi = d.minute.toString().padLeft(2, '0');
      return '$dd/$mm $hh:$mi';
    } catch (_) {
      return '';
    }
  }
}
