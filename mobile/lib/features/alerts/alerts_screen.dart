/// Mis avisos (issue N-1): centro de notificaciones de plantas, botánico y admin.
///
/// Polling 30 s SOLO con la pantalla visible (Timer en init/dispose + backoff
/// ante fallo); local-notify en error+warn nuevas con dedup por fingerprint;
/// caché offline con chip; badge de no-leídos reseteado al abrir.
library;

import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:mole_ai/core/errors.dart';
import 'package:mole_ai/core/notify.dart';
import 'package:mole_ai/core/offline_store.dart';
import 'package:mole_ai/features/alerts/alerts.dart';

class AlertsScreen extends ConsumerStatefulWidget {
  const AlertsScreen(
      {super.key,
      this.pollInterval = const Duration(seconds: 30),
      this.onNotify});

  /// Inyectable en tests (un Timer real de 30 s impediría pumpAndSettle).
  final Duration pollInterval;

  /// Seam de notificación (prod: NotifyService.show). Tests pasan un recorder.
  final Future<void> Function(String title, String body)? onNotify;

  @override
  ConsumerState<AlertsScreen> createState() => _AlertsScreenState();
}

class _AlertsScreenState extends ConsumerState<AlertsScreen> {
  Timer? _timer;
  int _failStreak = 0;
  bool _loading = true;
  bool _offline = false;
  String? _error;
  List<PlantAlert> _alerts = [];
  final Set<String> _seen = {};

  @override
  void initState() {
    super.initState();
    Future.microtask(() {
      ref.read(unreadAlertsProvider.notifier).reset();
      _load();
    });
    _timer = Timer(widget.pollInterval, _tick);
  }

  @override
  void dispose() {
    _timer?.cancel();
    super.dispose();
  }

  void _tick() {
    if (!mounted) return;
    _load(silent: true);
    final backoff = _failStreak > 0 && _failStreak < 4 ? _failStreak : 0;
    _timer = Timer(widget.pollInterval * (1 + backoff), _tick);
  }

  Future<void> _load({bool silent = false}) async {
    if (!silent && mounted) setState(() => _loading = true);
    try {
      final repo = ref.read(alertsRepositoryProvider);
      final fresh = await repo.myAlerts();
      final store = await ref.read(offlineStoreProvider.future);
      await store.put(OfflineStore.alertsKey(),
          {'alerts': [for (final a in fresh) _toCache(a)]});
      _announce(fresh);
      if (!mounted) return;
      setState(() {
        _alerts = fresh;
        _offline = false;
        _error = null;
        _loading = false;
        _failStreak = 0;
      });
    } on RetryableException {
      final store = await ref.read(offlineStoreProvider.future);
      final hit = await store.get(OfflineStore.alertsKey());
      if (!mounted) return;
      setState(() {
        _alerts = _fromCache(hit?.payload);
        _offline = true;
        _error = null;
        _loading = false;
        _failStreak++;
      });
    } on ApiException catch (e) {
      if (!mounted) return;
      setState(() {
        _error = e.message;
        _loading = false;
        _failStreak++;
      });
    } catch (_) {
      if (!mounted) return;
      setState(() {
        _error = 'Error inesperado. Intenta de nuevo.';
        _loading = false;
        _failStreak++;
      });
    }
  }

  /// Notifica error+warn nuevas (dedup); actualiza badge de no-leídos.
  void _announce(List<PlantAlert> fresh) {
    var freshUnread = 0;
    final notify = widget.onNotify ?? NotifyService.show;
    for (final a in fresh) {
      if (_seen.add(a.fingerprint) && a.notifiable) {
        freshUnread++;
        notify(
          a.severity == AlertSeverity.error ? 'Alerta en tu planta' : 'Aviso en tu planta',
          a.message,
        );
      }
    }
    if (freshUnread > 0) {
      ref.read(unreadAlertsProvider.notifier).add(freshUnread);
    }
  }

  Map<String, Object?> _toCache(PlantAlert a) => {
        'tipo': a.severity.name,
        'msg': a.message,
        'source': a.source,
        'recorded_at': a.recordedAt,
        'device_id': a.deviceId,
        'plant_id': a.plantId,
      };

  List<PlantAlert> _fromCache(Object? payload) {
    if (payload is! Map) return [];
    final list = payload['alerts'];
    if (list is! List) return [];
    return [
      for (final e in list)
        if (e is Map<String, dynamic>) PlantAlert.fromJson(e)
    ];
  }

  Color _color(AlertSeverity s, ColorScheme c) => switch (s) {
        AlertSeverity.error => c.error,
        AlertSeverity.warn => Colors.orange,
        AlertSeverity.info => c.primary,
      };

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Scaffold(
      appBar: AppBar(title: const Text('Mis avisos')),
      body: RefreshIndicator(
        onRefresh: () => _load(),
        child: _loading
            ? const Center(child: CircularProgressIndicator())
            : _error != null
                ? ListView(children: [
                    const SizedBox(height: 80),
                    Center(
                      child: Semantics(
                        liveRegion: true,
                        excludeSemantics: true,
                        label: 'Error: $_error',
                        child: Text(_error!,
                            style: TextStyle(color: scheme.error)),
                      ),
                    ),
                    const SizedBox(height: 12),
                    Center(
                      child: FilledButton(
                          onPressed: () => _load(),
                          child: const Text('Reintentar')),
                    ),
                  ])
                : _alerts.isEmpty
                    ? ListView(children: const [
                        SizedBox(height: 80),
                        Center(
                            child: Text(
                                'Sin avisos. Tus plantas están estables.')),
                      ])
                    : ListView(
                        children: [
                          if (_offline)
                            const Padding(
                              padding: EdgeInsets.all(8),
                              child: Chip(
                                avatar: Icon(Icons.cloud_off_outlined, size: 18),
                                label: Text('Sin conexión: últimos datos conocidos'),
                              ),
                            ),
                          for (final a in _alerts)
                            Semantics(
                              // Anuncio único: sin exclude, el lector repetiría
                              // el mensaje (label + título + subtítulo).
                              excludeSemantics: true,
                              label: a.recordedAt.isEmpty
                                  ? '${a.severity.name}: ${a.message}'
                                  : '${a.severity.name}: ${a.message}, ${a.recordedAt}',
                              child: ListTile(
                                leading: Icon(
                                  a.severity == AlertSeverity.error
                                      ? Icons.error_outline
                                      : a.severity == AlertSeverity.warn
                                          ? Icons.warning_amber_outlined
                                          : Icons.info_outline,
                                  color: _color(a.severity, scheme),
                                ),
                                title: Text(a.message),
                                subtitle: a.recordedAt.isEmpty
                                    ? null
                                    : Text(a.recordedAt),
                              ),
                            ),
                        ],
                      ),
      ),
    );
  }
}
