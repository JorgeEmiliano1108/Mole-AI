/// Clima para consulta agronómica (issue 15).
///
/// Reutiliza `MapRepository.currentWeather` (endpoint público). Selector
/// manual lat/lon + preset CDMX; sin geolocalización en v1 (sin permiso
/// LOCATION por decisión). Pestaña extra sugerida: mapa de hotspots.
library;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'package:mole_ai/core/errors.dart';
import 'package:mole_ai/features/map/map.dart';
import 'package:mole_ai/features/map/map_screen.dart' show mapRepositoryProvider;

String _friendly(Object e) => e is ApiException
    ? e.message
    : 'Error inesperado. Intenta de nuevo.';

const _presets = {
  'CDMX': (19.4326, -99.1332),
  'Guadalajara': (20.6597, -103.3496),
  'Monterrey': (25.6866, -100.3161),
};

class WeatherScreen extends ConsumerStatefulWidget {
  const WeatherScreen({super.key});

  @override
  ConsumerState<WeatherScreen> createState() => _WeatherScreenState();
}

class _WeatherScreenState extends ConsumerState<WeatherScreen> {
  String _city = 'CDMX';
  final _lat = TextEditingController(text: '19.4326');
  final _lon = TextEditingController(text: '-99.1332');
  CurrentWeather? _weather;
  bool _loading = false;
  String? _error;

  @override
  void dispose() {
    _lat.dispose();
    _lon.dispose();
    super.dispose();
  }

  Future<void> _load() async {
    final lat = double.tryParse(_lat.text.trim());
    final lon = double.tryParse(_lon.text.trim());
    if (lat == null || lon == null) {
      setState(() => _error = 'Coordenadas inválidas.');
      return;
    }
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final w = await ref
          .read(mapRepositoryProvider)
          .currentWeather(lat, lon);
      if (mounted) setState(() => _weather = w);
    } catch (e) {
      if (mounted) setState(() => _error = _friendly(e));
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  void initState() {
    super.initState();
    Future.microtask(_load);
  }

  @override
  Widget build(BuildContext context) {
    final w = _weather;
    return SafeArea(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            SegmentedButton<String>(
              segments: [
                for (final c in _presets.keys)
                  ButtonSegment(value: c, label: Text(c)),
              ],
              selected: {_city},
              onSelectionChanged: (s) {
                final coords = _presets[s.single]!;
                setState(() {
                  _city = s.single;
                  _lat.text = '${coords.$1}';
                  _lon.text = '${coords.$2}';
                });
                _load();
              },
            ),
            const SizedBox(height: 8),
            Row(
              children: [
                Expanded(
                    child: TextField(
                        controller: _lat,
                        decoration:
                            const InputDecoration(labelText: 'Latitud'),
                        keyboardType: const TextInputType.numberWithOptions(
                            signed: true, decimal: true))),
                const SizedBox(width: 8),
                Expanded(
                    child: TextField(
                        controller: _lon,
                        decoration:
                            const InputDecoration(labelText: 'Longitud'),
                        keyboardType: const TextInputType.numberWithOptions(
                            signed: true, decimal: true))),
                const SizedBox(width: 8),
                FilledButton(
                    style: FilledButton.styleFrom(
                        minimumSize: const Size(64, 48)),
                    onPressed: _loading ? null : _load,
                    child: const Text('Ver')),
              ],
            ),
            const SizedBox(height: 16),
            if (_loading)
              const Center(child: CircularProgressIndicator()),
            if (_error != null)
              Semantics(
                liveRegion: true,
                child: Text(_error!,
                    style: TextStyle(
                        color: Theme.of(context).colorScheme.error)),
              ),
            if (!_loading && _error == null && w != null)
              Card(
                child: Column(
                  children: [
                    ListTile(
                        title: const Text('Temperatura'),
                        trailing: Text(
                            '${w.temp?.toStringAsFixed(1) ?? '—'}°C')),
                    ListTile(
                        title: const Text('Humedad'),
                        trailing: Text(
                            '${w.humidity?.toStringAsFixed(0) ?? '—'}%')),
                    ListTile(
                        title: const Text('Condición'),
                        trailing:
                            Text(w.description ?? '—')),
                  ],
                ),
              ),
          ],
        ),
      ),
    );
  }
}
