/// Portal público Mole.AI (issue 14): entra sin login.
///
/// Hero con objetivo/filosofía, buscador de flora endémica (endpoint público
/// con caché offline + disclaimer NOM-059 obligatorio) y CTAs Entrar/Crear
/// cuenta. Sin token: ApiClient omite Bearer en estas rutas (contrato §0).
library;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import 'package:mole_ai/core/offline_store.dart';
import 'package:mole_ai/features/species/nom059_warning.dart';
import 'package:mole_ai/features/species/species.dart';
import 'package:mole_ai/features/species/species_search_screen.dart';

class PublicHomeScreen extends ConsumerStatefulWidget {
  const PublicHomeScreen({super.key});

  @override
  ConsumerState<PublicHomeScreen> createState() => _PublicHomeScreenState();
}

class _PublicHomeScreenState extends ConsumerState<PublicHomeScreen> {
  List<Species> _endemic = [];
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    Future.microtask(_loadEndemic);
  }

  Future<void> _loadEndemic() async {
    try {
      final store = await ref.read(offlineStoreProvider.future);
      final r = await ref
          .read(speciesRepositoryProvider)
          .searchCached('', store, endemic: true);
      if (mounted) setState(() => _endemic = r.results.take(6).toList());
    } catch (_) {
      // Portal degradado sin red ni caché: hero + CTAs siguen visibles.
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Scaffold(
      appBar: AppBar(
        title: const Text('Mole.AI'),
        actions: [
          TextButton(
              onPressed: () => context.go('/login'),
              child: const Text('Entrar')),
          FilledButton(
              onPressed: () => context.go('/registro'),
              child: const Text('Crear cuenta')),
        ],
      ),
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            Text('Monitoreo vivo de tu invernadero',
                style: Theme.of(context).textTheme.headlineSmall),
            const SizedBox(height: 8),
            const Text(
                'Mole.AI une sensores IoT, visión por computadora y '
                'conocimiento botánico para cuidar tus plantas. Tus datos '
                'son tuyos: consentimiento explícito, nada sin permiso.'),
            const SizedBox(height: 16),
            OutlinedButton.icon(
              onPressed: () => context.go('/especies-publico'),
              icon: const Icon(Icons.eco),
              label: const Text('Explorar flora endémica'),
            ),
            const SizedBox(height: 24),
            Text('Endémicas de México',
                style: Theme.of(context).textTheme.titleMedium),
            const SizedBox(height: 8),
            if (_loading)
              const Center(child: CircularProgressIndicator())
            else if (_endemic.isEmpty)
              const Text(
                  'Sin conexión ahora mismo. Entra a Flora para buscar con o sin red.'),
            for (final s in _endemic)
              Card(
                child: ListTile(
                  title: Text(s.nombre),
                  subtitle: Text(s.nombreCientifico),
                  trailing: s.isEndemic
                      ? Icon(Icons.verified, color: scheme.primary)
                      : null,
                ),
              ),
            const SizedBox(height: 8),
            for (final s in _endemic.take(1)) Nom059Warning(species: s),
          ],
        ),
      ),
    );
  }
}
