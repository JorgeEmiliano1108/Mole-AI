/// Diagnóstico por foto (contrato §5, vía async congelada).
///
/// Contenido (sin Scaffold): el [HomeShell] provee AppBar.
library;

import 'package:connectivity_plus/connectivity_plus.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:image_picker/image_picker.dart';
import 'package:mole_ai/core/errors.dart';
import 'package:mole_ai/core/notify.dart';
import 'package:mole_ai/core/offline_store.dart';
import 'package:mole_ai/features/auth/auth_controller.dart';
import 'package:mole_ai/features/vision/edge_ai.dart';
import 'package:mole_ai/features/vision/vision.dart';
import 'package:mole_ai/pvu/routing.dart';

final visionRepositoryProvider = Provider<VisionRepository>(
    (ref) => VisionRepository(ref.watch(apiClientProvider)));

String _friendly(Object e) => e is ApiException
    ? e.message
    : 'Error inesperado. Intenta de nuevo.';

class DiagnosisScreen extends ConsumerStatefulWidget {
  const DiagnosisScreen({super.key});

  @override
  ConsumerState<DiagnosisScreen> createState() => _DiagnosisScreenState();
}

class _DiagnosisScreenState extends ConsumerState<DiagnosisScreen> {
  String? _phase; // picked|uploading|polling|done|error
  String? _message;
  VisionStatus? _status;
  EdgeVerdict? _edge;
  String? _advice;
  int _pending = 0;

  bool get _busy => _phase == 'uploading' || _phase == 'polling';

  @override
  void initState() {
    super.initState();
    Future.microtask(_refreshPending);
  }

  Future<void> _refreshPending() async {
    try {
      final store = await ref.read(offlineStoreProvider.future);
      final n = (await store.pending()).length;
      if (mounted) setState(() => _pending = n);
    } catch (_) {}
  }

  Future<void> _drain() async {
    try {
      final store = await ref.read(offlineStoreProvider.future);
      final n =
          await ref.read(visionRepositoryProvider).drainQueue(store);
      if (!mounted) return;
      setState(() {
        _message = n > 0 ? 'Se subieron $n foto(s) pendiente(s).' : null;
        if (n > 0) _phase = null;
      });
      await _refreshPending();
    } catch (e) {
      if (!mounted) return;
      setState(() => _message = _friendly(e));
    }
  }

  Future<ConnectivityStatus> _currentConnectivity() async {
    final results = await Connectivity().checkConnectivity();
    if (results.isEmpty) return ConnectivityStatus.offline;
    final result = results.first;
    return switch (result) {
      ConnectivityResult.wifi || ConnectivityResult.ethernet =>
        ConnectivityStatus.online,
      ConnectivityResult.mobile => ConnectivityStatus.metered,
      _ => ConnectivityStatus.offline,
    };
  }

  Future<void> _submitToCloud(List<int> bytes, String filename) async {
    setState(() => _message = 'Enviando al servidor…');
    final taskId = await ref
        .read(visionRepositoryProvider)
        .submitDiagnosis(bytes, filename);
    if (!mounted) return;
    setState(() {
      _phase = 'polling';
      _message = 'Analizando…';
    });
    final status =
        await ref.read(visionRepositoryProvider).pollStatus(taskId);
    if (!mounted) return;
    setState(() {
      _phase = status.isFailure ? 'error' : 'done';
      _status = status;
      _message =
          status.isFailure ? (status.error ?? 'Falló el análisis.') : null;
    });
    if (status.isSuccess) {
      final d = status.diagnosis;
      await NotifyService.show('Diagnóstico listo',
          d?.speciesCommon ?? 'Revisa el resultado en la app.');
    }
  }

  Future<void> _showEdgeResult(EdgeVerdict edge, PvuRoute route,
      List<int> bytes, String filename) async {
    String? advice;
    try {
      final store = await ref.read(offlineStoreProvider.future);
      // Encolar resultado edge con la razón PVU para telemetría.
      await store.enqueueDiagnosis(bytes, filename,
          pvuReason: route.reason);
      advice = await store.getAdvice(edge.topClass.toString());
      await _refreshPending();
    } catch (_) {}
    if (!mounted) return;
    setState(() {
      _phase = 'done';
      _edge = edge;
      _advice = advice;
      _message = null;
    });
    await NotifyService.show('Diagnóstico listo (edge)',
        'Clase ${edge.topClass} · ${(edge.confidence * 100).toStringAsFixed(0)}% · ${edge.latencyMs.toStringAsFixed(0)}ms en dispositivo.');
  }

  Future<void> _pick(ImageSource source) async {
    final img = await ImagePicker().pickImage(
        source: source, maxWidth: 1600, imageQuality: 85);
    if (img == null) return;
    final imgName = img.name;
    List<int>? rawBytes;
    setState(() {
      _phase = 'uploading';
      _message = 'Analizando en el dispositivo…';
      _status = null;
      _edge = null;
    });
    try {
      final bytes = await img.readAsBytes();
      rawBytes = bytes;

      // PVU: decidir ruta ANTES de gastar batería/RAM en inferencia.
      final net = await _currentConnectivity();
      final pvuRoute = await route(net: net, batteryPct: 1.0, wifi: null);

      if (pvuRoute is CloudRoute) {
        await _submitToCloud(bytes, imgName);
        return;
      }

      // Local o Hybrid: intentar edge primero.
      EdgeVerdict? edge;
      try {
        edge = await EdgeAiService().diagnose(bytes);
      } catch (_) {
        edge = null; // TFLite no disponible.
      }
      if (!mounted) return;

      if (edge != null && edge.local) {
        await _showEdgeResult(edge, pvuRoute, bytes, imgName);
        return;
      }

      if (pvuRoute is LocalRoute) {
        // Sin red: mostramos el veredicto edge aunque sea incierto y encolamos.
        if (edge != null) {
          await _showEdgeResult(edge, pvuRoute, bytes, imgName);
        } else {
          setState(() => _message = 'No se pudo analizar sin conexión.');
        }
        return;
      }

      // Hybrid con edge incierto/no disponible → nube.
      await _submitToCloud(bytes, imgName);
    } catch (e) {
      if (!mounted) return;
      final queued = rawBytes;
      if (e is RetryableException && queued != null) {
        // Sin red: se encola la foto y se sube al volver la conexión.
        try {
          final store = await ref.read(offlineStoreProvider.future);
          await store.enqueueDiagnosis(queued, imgName);
          await _refreshPending();
          setState(() {
            _phase = null;
            _message =
                'Sin conexión: la foto quedó en cola y se subirá sola.';
          });
          return;
        } catch (_) {}
      }
      setState(() {
        _phase = 'error';
        _message = _friendly(e);
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final d = _status?.diagnosis;
    return SafeArea(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Row(
              children: [
                Expanded(
                  child: FilledButton.icon(
                    style: FilledButton.styleFrom(
                        minimumSize: const Size(64, 48)),
                    onPressed: _busy ? null : () => _pick(ImageSource.camera),
                    icon: const Icon(Icons.camera_alt),
                    label: const Text('Foto'),
                  ),
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: OutlinedButton.icon(
                    style: OutlinedButton.styleFrom(
                        minimumSize: const Size(64, 48)),
                    onPressed: _busy ? null : () => _pick(ImageSource.gallery),
                    icon: const Icon(Icons.photo),
                    label: const Text('Galería'),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 16),
            Align(
              alignment: Alignment.centerRight,
              child: TextButton.icon(
                onPressed: _busy
                    ? null
                    : () => context.go('/diagnostico/historial'),
                icon: const Icon(Icons.history, size: 18),
                label: const Text('Ver historial'),
              ),
            ),
            if (_busy)
              Center(
                child: Column(
                  children: [
                    const CircularProgressIndicator(),
                    const SizedBox(height: 8),
                    Text(_message ?? 'Procesando…'),
                  ],
                ),
              ),
            if (_phase == 'error' && _message != null) ...[
              Semantics(
                liveRegion: true,
                child: Text(_message!,
                    style: TextStyle(
                        color: Theme.of(context).colorScheme.error)),
              ),
              const SizedBox(height: 8),
              OutlinedButton(
                  onPressed: () =>
                      setState(() => _phase = null),
                  child: const Text('Reintentar')),
            ],
            if (_phase == 'done' && (_edge != null || d != null))
              Expanded(
                child: ListView(
                  children: [
                    if (_edge != null) ...[
                      Chip(
                        avatar: const Icon(Icons.memory, size: 18),
                        label: Text(
                            'Edge (offline) · ${_edge!.latencyMs.toStringAsFixed(0)}ms'),
                      ),
                      const SizedBox(height: 8),
                      Text('Clase detectada: ${_edge!.topClass}',
                          style:
                              Theme.of(context).textTheme.headlineSmall),
                      Text('Confianza: ${(_edge!.confidence * 100).toStringAsFixed(0)}%'),
                      const SizedBox(height: 8),
                      Text(
                          'Modelo de integración: si la confianza fuera menor, '
                          'la foto se enviaría al servidor.',
                          style: Theme.of(context).textTheme.bodySmall),
                    ],
                    if (d != null) ...[
                      Text(d.speciesCommon ?? 'Sin especie',
                          style:
                              Theme.of(context).textTheme.headlineSmall),
                      if (d.speciesScientific != null)
                      Text(d.speciesScientific!,
                          style: Theme.of(context).textTheme.bodySmall),
                    const SizedBox(height: 8),
                    Text('Afección: ${d.afflictionName ?? '—'} '
                        '(${d.severity ?? '—'})'),
                    Text('Confianza: ${d.confidence != null ? '${(d.confidence! * 100).toStringAsFixed(0)}%' : '—'}'),
                    Text('pH estimado: ${d.phPredicted?.toStringAsFixed(1) ?? '—'}'),
                    if (d.immediateActions.isNotEmpty) ...[
                      const SizedBox(height: 8),
                      Text('Acciones inmediatas:',
                          style: Theme.of(context).textTheme.titleSmall),
                      for (final a in d.immediateActions) Text('• $a'),
                    ],
                    if (d.disclaimer != null) ...[
                      const SizedBox(height: 8),
                      Text(d.disclaimer!,
                          style: Theme.of(context).textTheme.bodySmall),
                    ],
                  ],
                  if (_advice != null) ...[
                    const SizedBox(height: 12),
                    Text('Recomendación offline:',
                        style: Theme.of(context).textTheme.titleSmall),
                    Text(_advice!,
                        style: Theme.of(context).textTheme.bodySmall),
                  ],
                ],
              ),
            ),
            if (_phase == null) ...[
              if (_pending > 0)
                Padding(
                  padding: const EdgeInsets.only(bottom: 8),
                  child: Row(
                    children: [
                      Expanded(
                        child: Text(
                            '$_pending foto(s) en cola (sin conexión).'),
                      ),
                      OutlinedButton(
                          onPressed: _busy ? null : _drain,
                          child: const Text('Subir ahora')),
                    ],
                  ),
                ),
              // Guía ROI (P1): el modelo se entrenó con hojas encuadradas;
              // fondos complejos degradan accuracy. Sin segmentación en v1.
              AspectRatio(
                aspectRatio: 4 / 3,
                child: Container(
                  decoration: BoxDecoration(
                    border: Border.all(
                        color: Theme.of(context).colorScheme.primary,
                        width: 2),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: const Center(
                      child: Text('Encuadra la hoja aquí')),
                ),
              ),
              const SizedBox(height: 8),
              const Expanded(
                child: Center(
                  child: Text(
                      'Toma una foto de la planta.\nSe intenta en el dispositivo; si duda, va al servidor.',
                      textAlign: TextAlign.center),
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }
}
