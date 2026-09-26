/// Detalle de planta: ficha + última telemetría + salud del dispositivo.
library;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'package:mole_ai/core/errors.dart';
import 'package:mole_ai/core/offline_store.dart';
import 'package:mole_ai/features/plants/plants.dart';
import 'package:mole_ai/features/plants/telemetry_badge.dart';
import 'package:mole_ai/features/plants/plants_screen.dart'
    show plantsRepositoryProvider, telemetryRepositoryProvider;

String _friendly(Object e) => e is ApiException
    ? e.message
    : 'Error inesperado. Intenta de nuevo.';

String _fmt(double? v, String unit) =>
    v == null ? '—' : '${v.toStringAsFixed(1)} $unit';

class PlantDetailScreen extends ConsumerStatefulWidget {
  const PlantDetailScreen({super.key, required this.plantId});
  final String plantId;

  @override
  ConsumerState<PlantDetailScreen> createState() => _PlantDetailScreenState();
}

class _PlantDetailScreenState extends ConsumerState<PlantDetailScreen> {
  Plant? _plant;
  Telemetry? _telemetry;
  bool _loading = true;
  bool _offline = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    Future.microtask(_load);
  }

  Future<void> _load() async {
    if (mounted) setState(() => _loading = true);
    try {
      final store = await ref.read(offlineStoreProvider.future);
      final p = await ref
          .read(plantsRepositoryProvider)
          .detail(widget.plantId);
      Telemetry? t;
      var offline = false;
      try {
        final hit = await ref
            .read(telemetryRepositoryProvider)
            .latestCached(store, widget.plantId);
        t = hit.telemetry;
        offline = hit.offline;
      } catch (_) {}
      if (mounted) {
        setState(() {
          _plant = p;
          _telemetry = t;
          _offline = offline;
          _error = null;
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
    return Scaffold(
      appBar: AppBar(title: Text(_plant?.nickname ?? 'Planta')),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : _error != null
              ? Center(
                  child: Padding(
                    padding: const EdgeInsets.all(24),
                    child: Column(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Semantics(
                          liveRegion: true,
                          excludeSemantics: true,
                          label: 'Error: $_error',
                          child: Text(_error!,
                              textAlign: TextAlign.center,
                              style: TextStyle(
                                  color: Theme.of(context).colorScheme.error)),
                        ),
                        const SizedBox(height: 12),
                        FilledButton(
                            onPressed: _load,
                            child: const Text('Reintentar')),
                      ],
                    ),
                  ),
                )
              : ListView(
                  padding: const EdgeInsets.all(16),
                  children: [
                    if (_offline)
                      const Padding(
                        padding: EdgeInsets.only(bottom: 8),
                        child: Chip(
                          avatar:
                              Icon(Icons.cloud_off_outlined, size: 18),
                          label: Text(
                              'Sin conexión: últimos datos conocidos'),
                        ),
                      ),
                    if (_telemetry?.hasData != true)
                      const Card(
                          child: ListTile(
                              title: Text(
                                  'Sin datos (nodo sin logs)'))),
                    if (_telemetry?.hasData == true) ...[
                      Align(
                        alignment: Alignment.centerLeft,
                        child: TelemetrySourceBadge(
                            source: _telemetry!.source),
                      ),
                      const SizedBox(height: 8),
                      Card(
                        child: Column(
                          children: [
                            ListTile(
                                title: const Text('Suelo'),
                                trailing: Text(_fmt(
                                    _telemetry!.soilHumidity, '%'))),
                            ListTile(
                                title: const Text('Aire'),
                                trailing: Text(_fmt(
                                    _telemetry!.airTemperature, '°C'))),
                            ListTile(
                                title: const Text('Humedad aire'),
                                trailing: Text(_fmt(
                                    _telemetry!.airHumidity, '%'))),
                            ListTile(
                                title: const Text('UV'),
                                trailing: Text(_fmt(
                                    _telemetry!.uvIndex, ''))),
                            ListTile(
                                title: const Text('pH'),
                                trailing: Text(_fmt(
                                    _telemetry!.phLevel, ''))),
                          ],
                        ),
                      ),
                      Text(
                          'Medido: ${_telemetry!.recordedAt ?? '—'}',
                          style: Theme.of(context).textTheme.bodySmall),
                    ],
                  ],
                ),
    );
  }
}
