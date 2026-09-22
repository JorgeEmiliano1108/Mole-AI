/// Buscador de especies (contrato §2) con aviso NOM-059 integrado.
///
/// Contenido (sin Scaffold): el [HomeShell] provee AppBar + logout único.
library;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:mole_ai/core/errors.dart';
import 'package:mole_ai/core/offline_store.dart';
import 'package:mole_ai/features/auth/auth_controller.dart';
import 'package:mole_ai/features/species/nom059_warning.dart';
import 'package:mole_ai/features/species/species.dart';

final speciesRepositoryProvider = Provider<SpeciesRepository>(
    (ref) => SpeciesRepository(ref.watch(apiClientProvider)));

String _friendly(Object e) => e is ApiException
    ? e.message
    : 'Error inesperado. Intenta de nuevo.';

class SpeciesSearchScreen extends ConsumerStatefulWidget {
  /// `publicMode`: envuelve en Scaffold propio (portal sin login).
  /// En falso es contenido del [HomeShell] (provee AppBar).
  const SpeciesSearchScreen({super.key, this.publicMode = false});

  final bool publicMode;

  @override
  ConsumerState<SpeciesSearchScreen> createState() =>
      _SpeciesSearchScreenState();
}

class _SpeciesSearchScreenState extends ConsumerState<SpeciesSearchScreen> {
  final _q = TextEditingController();
  List<Species> _results = [];
  bool _loading = false;
  bool _searched = false;
  bool _offline = false;
  String? _error;

  @override
  void dispose() {
    _q.dispose();
    super.dispose();
  }

  Future<void> _search() async {
    final query = _q.text.trim();
    if (query.isEmpty || _loading) return;
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final store = await ref.read(offlineStoreProvider.future);
      final r = await ref
          .read(speciesRepositoryProvider)
          .searchCached(query, store);
      if (mounted) {
        setState(() {
          _results = r.results;
          _searched = true;
          _offline = r.offline;
        });
      }
    } catch (e) {
      if (mounted) setState(() => _error = _friendly(e));
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final body = SafeArea(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          children: [
            Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: _q,
                    decoration: const InputDecoration(
                        labelText: 'Buscar (nombre común o científico)'),
                    textInputAction: TextInputAction.search,
                    onSubmitted: (_) => _search(),
                  ),
                ),
                const SizedBox(width: 8),
                FilledButton(
                    style: FilledButton.styleFrom(
                        minimumSize: const Size(64, 48)),
                    onPressed: _loading ? null : _search,
                    child: const Text('Buscar')),
              ],
            ),
            if (_error != null) ...[
              const SizedBox(height: 8),
              Semantics(
                liveRegion: true,
                child: Text(_error!,
                    style: TextStyle(
                        color: Theme.of(context).colorScheme.error)),
              ),
              const SizedBox(height: 4),
              OutlinedButton(
                  onPressed: _search, child: const Text('Reintentar')),
            ],
            const SizedBox(height: 8),
            Expanded(
              child: _loading
                  ? const Center(child: CircularProgressIndicator())
                  : !_searched
                      ? const Center(
                          child: Text(
                              'Busca una especie para ver su ficha y avisos.'))
                      : Column(
                          children: [
                            if (_offline)
                              const Padding(
                                padding: EdgeInsets.only(bottom: 8),
                                child: Chip(
                                  avatar: Icon(Icons.cloud_off, size: 18),
                                  label: Text(
                                      'Sin conexión: mostrando caché'),
                                ),
                              ),
                            Expanded(
                              child: _results.isEmpty
                                  ? const Center(
                                      child: Text(
                                          'Sin resultados para esa búsqueda.'))
                                  : ListView.builder(
                                      itemCount: _results.length,
                                      itemBuilder: (context, i) {
                                        final s = _results[i];
                                        return Card(
                                          child: Padding(
                                            padding:
                                                const EdgeInsets.all(12),
                                            child: Column(
                                              crossAxisAlignment:
                                                  CrossAxisAlignment.start,
                                              children: [
                                                Text(s.nombre,
                                                    style: Theme.of(context)
                                                        .textTheme
                                                        .titleMedium),
                                                Text(s.nombreCientifico,
                                                    style: Theme.of(context)
                                                        .textTheme
                                                        .bodySmall),
                                                Nom059Warning(species: s),
                                              ],
                                            ),
                                          ),
                                        );
                                      },
                                    ),
                            ),
                          ],
                        ),
            ),
          ],
        ),
      ),
    );
    if (!widget.publicMode) return body;
    return Scaffold(
      appBar: AppBar(
        title: const Text('Flora'),
        actions: [
          TextButton(
            onPressed: () => context.go('/login'),
            child: const Text('Entrar'),
          ),
        ],
      ),
      body: body,
    );
  }
}
