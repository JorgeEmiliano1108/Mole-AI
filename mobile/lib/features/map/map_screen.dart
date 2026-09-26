/// Pantalla de mapa: hotspots del usuario sobre CartoDB dark (contrato §6).
library;

import 'package:flutter/material.dart';
import 'package:flutter_map/flutter_map.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:latlong2/latlong.dart';
import 'package:mole_ai/core/errors.dart';
import 'package:mole_ai/features/auth/auth_controller.dart';
import 'package:mole_ai/features/map/map.dart';

final mapRepositoryProvider = Provider<MapRepository>(
    (ref) => MapRepository(ref.watch(apiClientProvider)));

String _friendly(Object e) => e is ApiException
    ? e.message
    : 'Error inesperado. Intenta de nuevo.';

Color _severityColor(String severity, BuildContext context) {
  final scheme = Theme.of(context).colorScheme;
  return switch (severity) {
    'high' => scheme.error,
    'medium' => Colors.orange,
    _ => scheme.primary,
  };
}

class MapScreen extends ConsumerStatefulWidget {
  const MapScreen({super.key});

  @override
  ConsumerState<MapScreen> createState() => _MapScreenState();
}

class _MapScreenState extends ConsumerState<MapScreen> {
  List<Hotspot> _hotspots = [];
  bool _loading = true;
  String? _error;

  static const _defaultCenter = LatLng(19.4326, -99.1332); // CDMX

  @override
  void initState() {
    super.initState();
    Future.microtask(_load);
  }

  Future<void> _load() async {
    try {
      final hs = await ref.read(mapRepositoryProvider).hotspots();
      if (mounted) {
        setState(() {
          _hotspots = hs;
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
                  onPressed: () {
                    setState(() {
                      _loading = true;
                      _error = null;
                    });
                    _load();
                  },
                  child: const Text('Reintentar')),
            ],
          ),
        ),
      );
    }
    final center = _hotspots.isNotEmpty
        ? LatLng(_hotspots.first.lat, _hotspots.first.lng)
        : _defaultCenter;
    final map = FlutterMap(
      options: MapOptions(initialCenter: center, initialZoom: 11),
      children: [
        TileLayer(
          urlTemplate:
              'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png',
          subdomains: const ['a', 'b', 'c', 'd'],
        ),
        MarkerLayer(
          markers: [
            for (final h in _hotspots)
              Marker(
                point: LatLng(h.lat, h.lng),
                width: 40,
                height: 40,
                child: Semantics(
                  // Severidad también en texto (RNF-UX01): el color solo
                  // no informa a lector de pantalla ni a daltónicos.
                  excludeSemantics: true,
                  label:
                      '${h.species ?? 'Hotspot'}, severidad ${h.severity}',
                  child: Tooltip(
                    message:
                        '${h.species ?? 'Hotspot'} (${h.severity})',
                    child: Icon(Icons.location_on,
                        color: _severityColor(h.severity, context),
                        size: 36),
                  ),
                ),
              ),
          ],
        ),
      ],
    );
    return Stack(
      children: [
        map,
        if (_hotspots.isEmpty)
          Positioned(
            left: 16,
            right: 16,
            bottom: 24,
            child: Card(
              child: Padding(
                padding: const EdgeInsets.all(12),
                child: Text(
                  'Sin hotspots en esta zona. Mapa de CDMX sin marcadores.',
                  textAlign: TextAlign.center,
                  style: Theme.of(context).textTheme.bodyMedium,
                ),
              ),
            ),
          ),
      ],
    );
  }
}
