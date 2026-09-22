/// Inicio dashboard (issue 15): resumen operativo de un vistazo.
///
/// Reutiliza repos existentes: colección + última telemetría + clima demo
/// (CDMX) + accesos a Diagnóstico/Chat. Solo lectura.
library;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import 'package:mole_ai/core/errors.dart';
import 'package:mole_ai/core/offline_store.dart';
import 'package:mole_ai/features/map/map.dart';
import 'package:mole_ai/features/map/map_screen.dart' show mapRepositoryProvider;
import 'package:mole_ai/features/plants/plants.dart';
import 'package:mole_ai/features/plants/plants_screen.dart'
    show plantsRepositoryProvider, telemetryRepositoryProvider;

String _friendly(Object e) => e is ApiException
    ? e.message
    : 'Error inesperado. Intenta de nuevo.';

class HomeDashboardScreen extends ConsumerStatefulWidget {
  const HomeDashboardScreen({super.key});

  @override
  ConsumerState<HomeDashboardScreen> createState() =>
      _HomeDashboardScreenState();
}

class _HomeDashboardScreenState extends ConsumerState<HomeDashboardScreen> {
  List<Plant> _plants = [];
  final _tele = <String, Telemetry>{};
  CurrentWeather? _weather;
  bool _loading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    Future.microtask(_load);
  }

  Future<void> _load() async {
    try {
      final store = await ref.read(offlineStoreProvider.future);
      final col = await ref
          .read(plantsRepositoryProvider)
          .myCollectionCached(store);
      final teleRepo = ref.read(telemetryRepositoryProvider);
      for (final p in col.plants) {
        try {
          final r = await teleRepo.latestCached(store, p.id);
          if (r.telemetry != null) _tele[p.id] = r.telemetry!;
        } catch (_) {}
      }
      try {
        _weather = await ref
            .read(mapRepositoryProvider)
            .currentWeather(19.4326, -99.1332);
      } catch (_) {}
      if (mounted) {
        setState(() {
          _plants = col.plants;
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
                        color: Theme.of(context).colorScheme.error))),
            const SizedBox(height: 12),
            OutlinedButton(onPressed: _load, child: const Text('Reintentar')),
          ],
        ),
      );
    }
    final withData =
        _plants.where((p) => _tele[p.id]?.hasData == true).length;
    return RefreshIndicator(
      onRefresh: _load,
      child: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          Card(
            child: ListTile(
              leading: const Icon(Icons.spa),
              title: Text(
                  '${_plants.length} plantas · $withData con datos'),
              subtitle: _weather == null
                  ? const Text('Clima no disponible')
                  : Text(
                      'CDMX: ${_weather!.temp?.toStringAsFixed(1) ?? '—'}°C'
                      '${_weather!.description != null ? ' · ${_weather!.description}' : ''}'),
            ),
          ),
          const SizedBox(height: 8),
          Row(
            children: [
              Expanded(
                child: FilledButton.icon(
                  onPressed: () => context.go('/diagnostico'),
                  icon: const Icon(Icons.camera_alt),
                  label: const Text('Diagnosticar'),
                ),
              ),
              const SizedBox(width: 8),
              Expanded(
                child: OutlinedButton.icon(
                  onPressed: () => context.go('/chat'),
                  icon: const Icon(Icons.chat),
                  label: const Text('Preguntar'),
                ),
              ),
            ],
          ),
          const SizedBox(height: 8),
          for (final p in _plants.take(5))
            Card(
              child: ListTile(
                title: Text(p.nickname.isEmpty ? '(sin nombre)' : p.nickname),
                subtitle: Text(_tele[p.id]?.hasData == true
                    ? 'Suelo ${_tele[p.id]!.soilHumidity?.toStringAsFixed(1) ?? '—'}% · '
                        'Aire ${_tele[p.id]!.airTemperature?.toStringAsFixed(1) ?? '—'}°C'
                    : 'Sin datos'),
                trailing: const Icon(Icons.chevron_right),
                onTap: () => context.go('/plantas/${p.id}'),
              ),
            ),
        ],
      ),
    );
  }
}
