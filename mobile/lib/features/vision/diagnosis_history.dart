/// Historial de diagnósticos (usa `VisionRepository.history` existente).
library;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'package:mole_ai/core/errors.dart';
import 'package:mole_ai/features/vision/diagnosis_screen.dart'
    show visionRepositoryProvider;

String _friendly(Object e) => e is ApiException
    ? e.message
    : 'Error inesperado. Intenta de nuevo.';

class DiagnosisHistoryScreen extends ConsumerStatefulWidget {
  const DiagnosisHistoryScreen({super.key});

  @override
  ConsumerState<DiagnosisHistoryScreen> createState() =>
      _DiagnosisHistoryScreenState();
}

class _DiagnosisHistoryScreenState
    extends ConsumerState<DiagnosisHistoryScreen> {
  List<Map<String, dynamic>> _items = [];
  bool _loading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    Future.microtask(_load);
  }

  Future<void> _load() async {
    try {
      final items =
          await ref.read(visionRepositoryProvider).history();
      if (mounted) {
        setState(() {
          _items = items;
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
    return Scaffold(
      appBar: AppBar(title: const Text('Historial')),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : _error != null
              ? Center(
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Semantics(
                        liveRegion: true,
                        child: Text(_error!,
                            style: TextStyle(
                                color: Theme.of(context)
                                    .colorScheme
                                    .error)),
                      ),
                      const SizedBox(height: 12),
                      OutlinedButton(
                          onPressed: _load,
                          child: const Text('Reintentar')),
                    ],
                  ),
                )
              : _items.isEmpty
                  ? const Center(
                      child: Text('Sin diagnósticos todavía.'))
                  : ListView.builder(
                      padding: const EdgeInsets.all(12),
                      itemCount: _items.length,
                      itemBuilder: (context, i) {
                        final h = _items[i];
                        return Card(
                          child: ListTile(
                            title: Text(
                                '${h['condition'] ?? h['diagnosis'] ?? 'Diagnóstico'}'),
                            subtitle: Text(
                                '${h['analyzed_at'] ?? h['created_at'] ?? ''}'),
                          ),
                        );
                      },
                    ),
    );
  }
}
