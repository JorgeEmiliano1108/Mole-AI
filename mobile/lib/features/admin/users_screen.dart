/// Usuarios admin (issue 15): tabla, búsqueda, cambio de rol y desactivado.
///
/// Backend: `GET admin/users/` + `PATCH/DELETE admin/users/<id>/` (soft).
/// Solo Superadmin otorga Superadmin o toca Superadmin (403 si no).
library;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'package:mole_ai/core/errors.dart';
import 'package:mole_ai/features/admin/admin.dart';
import 'package:mole_ai/features/admin/admin_error_panel.dart';
import 'package:mole_ai/features/admin/admin_metrics.dart'
    show adminRepositoryProvider;

String _friendly(Object e) => e is ApiException
    ? e.message
    : 'Error inesperado. Intenta de nuevo.';

const _roles = ['Operador', 'Admin', 'Superadmin'];

class UsersScreen extends ConsumerStatefulWidget {
  const UsersScreen({super.key});

  @override
  ConsumerState<UsersScreen> createState() => _UsersScreenState();
}

class _UsersScreenState extends ConsumerState<UsersScreen> {
  final _search = TextEditingController();
  List<ManagedUser> _users = [];
  bool _loading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    Future.microtask(_load);
  }

  @override
  void dispose() {
    _search.dispose();
    super.dispose();
  }

  Future<void> _load() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final users = await ref
          .read(adminRepositoryProvider)
          .users(search: _search.text.trim().isEmpty ? null : _search.text.trim());
      if (mounted) {
        setState(() {
          _users = users;
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

  Future<void> _changeRole(ManagedUser u) async {
    final next = await showDialog<String>(
      context: context,
      builder: (context) => SimpleDialog(
        title: Text('Rol de ${u.username}'),
        children: [
          for (final r in _roles)
            SimpleDialogOption(
              onPressed: () => Navigator.of(context).pop(r),
              child: Text(r),
            ),
        ],
      ),
    );
    if (next == null || !mounted) return;
    try {
      await ref
          .read(adminRepositoryProvider)
          .updateUser(u.id, role: next);
      await _load();
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Rol de ${u.username} actualizado a $next')),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text(_friendly(e))));
      }
    }
  }

  Future<void> _toggleActive(ManagedUser u) async {
    final confirm = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: Text(u.isActive ? 'Desactivar cuenta' : 'Reactivar cuenta'),
        content: Text(
            '${u.username} ${u.isActive ? 'no podrá entrar' : 'volverá a entrar'}.'),
        actions: [
          TextButton(
              onPressed: () => Navigator.of(context).pop(false),
              child: const Text('Cancelar')),
          FilledButton(
              onPressed: () => Navigator.of(context).pop(true),
              child: const Text('Confirmar')),
        ],
      ),
    );
    if (confirm != true || !mounted) return;
    try {
      await ref
          .read(adminRepositoryProvider)
          .updateUser(u.id, isActive: !u.isActive);
      await _load();
      if (mounted) {
        final msg = u.isActive
            ? 'Usuario ${u.username} desactivado'
            : 'Usuario ${u.username} reactivado';
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(msg)));
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text(_friendly(e))));
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Scaffold(
      appBar: AppBar(
        title: const Text('Usuarios'),
      ),
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Row(
                crossAxisAlignment: CrossAxisAlignment.end,
                children: [
                  Expanded(
                    child: TextField(
                      controller: _search,
                      decoration: const InputDecoration(
                        labelText: 'Buscar usuario o correo',
                        prefixIcon: Icon(Icons.search),
                        border: OutlineInputBorder(),
                      ),
                      textInputAction: TextInputAction.search,
                      onSubmitted: (_) => _load(),
                    ),
                  ),
                  const SizedBox(width: 8),
                  FilledButton(
                    style: FilledButton.styleFrom(
                      minimumSize: const Size(64, 48),
                    ),
                    onPressed: _loading ? null : _load,
                    child: const Text('Ver'),
                  ),
                ],
              ),
              const SizedBox(height: 16),
              Expanded(
                child: _loading
                    ? const Center(child: CircularProgressIndicator())
                    : _error != null
                        ? AdminErrorPanel(
                            message: _error!, onRetry: _load)
                        : _users.isEmpty
                            ? Center(
                                child: Column(
                                  mainAxisSize: MainAxisSize.min,
                                  children: [
                                    Icon(Icons.people_outline,
                                        size: 48,
                                        color: theme.colorScheme.outline),
                                    const SizedBox(height: 12),
                                    Text(
                                      'Sin usuarios.',
                                      style: theme.textTheme.titleMedium,
                                    ),
                                  ],
                                ),
                              )
                            : RefreshIndicator(
                                onRefresh: _load,
                                child: ListView.builder(
                                  itemCount: _users.length,
                                  itemBuilder: (context, i) {
                                    final u = _users[i];
                                    return Card(
                                      child: Semantics(
                                        label:
                                            "${u.username}, rol ${u.role ?? 'sin rol'}, ${u.isActive ? 'activo' : 'inactivo'}",
                                        child: ListTile(
                                          leading: Icon(
                                              u.isActive
                                                  ? Icons.person
                                                  : Icons.person_off,
                                              color: u.isActive
                                                  ? null
                                                  : theme.colorScheme.error),
                                          title: Text(u.username),
                                          subtitle: Column(
                                            crossAxisAlignment:
                                                CrossAxisAlignment.start,
                                            children: [
                                              Text(
                                                  '${u.role ?? '—'}${u.email != null ? ' · ${u.email}' : ''}'),
                                              if (!u.isActive)
                                                Chip(
                                                  avatar: const Icon(
                                                      Icons.cancel_outlined,
                                                      size: 16),
                                                  label: const Text('Inactivo'),
                                                  visualDensity:
                                                      VisualDensity.compact,
                                                ),
                                            ],
                                          ),
                                          trailing: PopupMenuButton<String>(
                                            onSelected: (v) {
                                              if (v == 'rol') {
                                                _changeRole(u);
                                              } else {
                                                _toggleActive(u);
                                              }
                                            },
                                            itemBuilder: (context) => [
                                              const PopupMenuItem(
                                                  value: 'rol',
                                                  child: Text('Cambiar rol')),
                                              PopupMenuItem(
                                                  value: 'activo',
                                                  child: Text(u.isActive
                                                      ? 'Desactivar'
                                                      : 'Reactivar')),
                                            ],
                                          ),
                                        ),
                                      ),
                                    );
                                  },
                                ),
                              ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
