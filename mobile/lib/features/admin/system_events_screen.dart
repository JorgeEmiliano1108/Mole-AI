/// Centro de fallas del sistema, SOLO admin (issue N-2).
///
/// Fuente: `GET admin/system-events` (4 secciones). Sin auto-polling: el centro
/// es una foto bajo demanda con pull-to-refresh (el polling 30 s vive en
/// Mis avisos; aquí el admin investiga). Doble gate: drawer + router.
library;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:mole_ai/core/errors.dart';
import 'package:mole_ai/features/admin/admin.dart';
import 'package:mole_ai/features/admin/admin_metrics.dart';

IconData _icon(String severity) => switch (severity) {
      'error' || 'critical' => Icons.error_outline,
      'warn' => Icons.warning_amber_outlined,
      _ => Icons.info_outline,
    };

Color _color(String severity, ColorScheme c) => switch (severity) {
      'error' || 'critical' => c.error,
      'warn' => c.secondary,
      _ => c.primary,
    };

class SystemEventsScreen extends ConsumerStatefulWidget {
  const SystemEventsScreen({super.key});

  @override
  ConsumerState<SystemEventsScreen> createState() => _SystemEventsScreenState();
}

class _SystemEventsScreenState extends ConsumerState<SystemEventsScreen> {
  bool _loading = true;
  String? _error;
  SystemEvents? _events;

  @override
  void initState() {
    super.initState();
    Future.microtask(_load);
  }

  Future<void> _load() async {
    if (mounted) setState(() => _loading = true);
    try {
      final events = await ref.read(adminRepositoryProvider).systemEvents();
      if (!mounted) return;
      setState(() {
        _events = events;
        _error = null;
        _loading = false;
      });
    } on ApiException catch (e) {
      if (!mounted) return;
      setState(() {
        _error = e.message;
        _loading = false;
      });
    } catch (_) {
      if (!mounted) return;
      setState(() {
        _error = 'Error inesperado. Intenta de nuevo.';
        _loading = false;
      });
    }
  }

  Widget _section(
      BuildContext context, String title, List<SystemEvent> items) {
    final scheme = Theme.of(context).colorScheme;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Padding(
          padding: const EdgeInsets.fromLTRB(16, 16, 16, 4),
          child: Text(title,
              style: Theme.of(context)
                  .textTheme
                  .titleMedium
                  ?.copyWith(fontWeight: FontWeight.bold)),
        ),
        if (items.isEmpty)
          const ListTile(
              leading: Icon(Icons.check_circle_outline),
              title: Text('Sin eventos en esta sección.')),
        for (final e in items)
          Semantics(
            excludeSemantics: true,
            label: '${e.severity}: ${e.title}'
                '${e.detail.isEmpty ? '' : ', ${e.detail}'}',
            child: ListTile(
              leading: Icon(_icon(e.severity),
                  color: _color(e.severity, scheme)),
              title: Text(e.title),
              subtitle: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(e.severity.toUpperCase(),
                      style: Theme.of(context)
                          .textTheme
                          .labelSmall
                          ?.copyWith(
                            color: _color(e.severity, scheme),
                            fontWeight: FontWeight.bold,
                          )),
                  if (e.detail.isNotEmpty) Text(e.detail),
                  if (e.timestamp.isNotEmpty) Text(e.timestamp),
                ],
              ),
            ),
          ),
      ],
    );
  }

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Scaffold(
      appBar: AppBar(title: const Text('Centro de fallas')),
      body: RefreshIndicator(
        onRefresh: _load,
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
                                style: TextStyle(color: scheme.error)))),
                    const SizedBox(height: 12),
                    Center(
                        child: FilledButton(
                            onPressed: _load,
                            child: const Text('Reintentar'))),
                  ])
                : ListView(children: [
                    _section(context, 'Seguridad', _events!.security),
                    _section(context, 'Dispositivos', _events!.devices),
                    _section(context, 'Telemetría', _events!.telemetry),
                    _section(context, 'Servicios', _events!.services),
                  ]),
      ),
    );
  }
}
