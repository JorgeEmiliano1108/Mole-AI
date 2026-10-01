/// Auditoría legible, SOLO admin (issue N-2).
///
/// Fuente: `GET admin/audit-log` (append-only en backend) con filtros
/// por acción y usuario. Doble gate: drawer + router.
library;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:mole_ai/core/errors.dart';
import 'package:mole_ai/features/admin/admin.dart';
import 'package:mole_ai/features/admin/admin_error_panel.dart';
import 'package:mole_ai/features/admin/admin_metrics.dart';

class AuditScreen extends ConsumerStatefulWidget {
  const AuditScreen({super.key});

  @override
  ConsumerState<AuditScreen> createState() => _AuditScreenState();
}

class _AuditScreenState extends ConsumerState<AuditScreen> {
  final _actionCtrl = TextEditingController();
  final _userCtrl = TextEditingController();
  bool _loading = true;
  String? _error;
  AuditPage _page = AuditPage();

  @override
  void initState() {
    super.initState();
    Future.microtask(_load);
  }

  @override
  void dispose() {
    _actionCtrl.dispose();
    _userCtrl.dispose();
    super.dispose();
  }

  Future<void> _load() async {
    if (mounted) setState(() => _loading = true);
    try {
      final page = await ref.read(adminRepositoryProvider).auditLog(
            action: _actionCtrl.text.trim(),
            userId: _userCtrl.text.trim(),
          );
      if (!mounted) return;
      setState(() {
        _page = page;
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
    return Scaffold(
      appBar: AppBar(title: const Text('Auditoría')),
      body: RefreshIndicator(
        onRefresh: _load,
        child: _loading
            ? const Center(child: CircularProgressIndicator())
            : ListView(children: [
                Padding(
                  padding: const EdgeInsets.all(12),
                  child: Row(children: [
                    Expanded(
                        child: TextField(
                      controller: _actionCtrl,
                      decoration: const InputDecoration(
                          labelText: 'Acción (ej. ADMIN)'),
                    )),
                    const SizedBox(width: 8),
                    Expanded(
                        child: TextField(
                      controller: _userCtrl,
                      keyboardType: TextInputType.number,
                      decoration: const InputDecoration(
                          labelText: 'Usuario (id)'),
                    )),
                    IconButton(
                      icon: const Icon(Icons.search),
                      tooltip: 'Filtrar',
                      onPressed: _load,
                    ),
                  ]),
                ),
                if (_error != null)
                  AdminErrorPanel(message: _error!, onRetry: _load)
                else if (_page.results.isEmpty)
                  const Padding(
                    padding: EdgeInsets.all(32),
                    child: Center(
                        child:
                            Text('Sin registros para esos filtros.')),
                  )
                else
                  for (final e in _page.results)
                    Semantics(
                      excludeSemantics: true,
                      label:
                          '${e.action}, usuario ${e.userId ?? 'sistema'}, ${e.timestamp}',
                      child: ListTile(
                        leading: const Icon(Icons.history_outlined),
                        title: Text(e.action),
                        subtitle: Text(
                            'Usuario: ${e.userId ?? '—'} · IP: ${e.ipAddress.isEmpty ? '—' : e.ipAddress}'
                            '${e.details.isEmpty ? '' : '\n${e.details}'}'
                            '${e.timestamp.isEmpty ? '' : '\n${e.timestamp}'}'),
                      ),
                    ),
                Padding(
                  padding: const EdgeInsets.all(16),
                  child: Center(
                      child: Text('${_page.count} registro(s)',
                          style: Theme.of(context).textTheme.bodySmall)),
                ),
              ]),
      ),
    );
  }
}
