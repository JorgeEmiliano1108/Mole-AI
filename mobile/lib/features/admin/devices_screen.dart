/// Dispositivos de la flota, SOLO admin (issue N-2).
///
/// Fuente: `GET admin/devices/` (sin tokens). Doble gate: drawer + router.
library;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:mole_ai/core/errors.dart';
import 'package:mole_ai/features/admin/admin.dart';
import 'package:mole_ai/features/admin/admin_metrics.dart';

class DevicesScreen extends ConsumerStatefulWidget {
  const DevicesScreen({super.key});

  @override
  ConsumerState<DevicesScreen> createState() => _DevicesScreenState();
}

class _DevicesScreenState extends ConsumerState<DevicesScreen> {
  bool _loading = true;
  String? _error;
  List<ManagedDevice> _devices = [];

  @override
  void initState() {
    super.initState();
    Future.microtask(_load);
  }

  Future<void> _load() async {
    if (mounted) setState(() => _loading = true);
    try {
      final devices = await ref.read(adminRepositoryProvider).devices();
      if (!mounted) return;
      setState(() {
        _devices = devices;
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

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    IconData icon(String s) => switch (s) {
          'online' => Icons.wifi,
          'warning' => Icons.wifi_off_outlined,
          'offline' => Icons.cloud_off_outlined,
          _ => Icons.help_outline,
        };
    return Scaffold(
      appBar: AppBar(title: const Text('Dispositivos')),
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
                : _devices.isEmpty
                    ? ListView(children: const [
                        SizedBox(height: 80),
                        Center(child: Text('Sin dispositivos registrados.')),
                      ])
                    : ListView(children: [
                        for (final d in _devices)
                          Semantics(
                            excludeSemantics: true,
                            label:
                                '${d.name}, estado ${d.status}, dueño ${d.owner.isEmpty ? 'desconocido' : d.owner}',
                            child: ListTile(
                              leading: Icon(icon(d.status)),
                              title: Text(d.name),
                              subtitle: Text(
                                  'Estado: ${d.status} · Dueño: ${d.owner.isEmpty ? '—' : d.owner}'
                                  '${d.lastSeen.isEmpty ? '' : '\nÚltimo contacto: ${d.lastSeen}'}'),
                            ),
                          ),
                      ]),
      ),
    );
  }
}
