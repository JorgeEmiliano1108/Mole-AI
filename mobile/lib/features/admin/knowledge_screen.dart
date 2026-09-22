/// Base de conocimiento RAG (issue 15): adjuntar + confirmar + listar.
///
/// Flujo presigned en 3 pasos (contrato §6b): request → PUT directo →
/// confirm (+poll de estado en lista). Solo admin (el backend exige
/// `IsAdminUser`; 403 si no).
library;

import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'package:mole_ai/core/errors.dart';
import 'package:mole_ai/features/admin/admin.dart';
import 'package:mole_ai/features/auth/auth_controller.dart';

final knowledgeRepositoryProvider = Provider<KnowledgeRepository>(
    (ref) => KnowledgeRepository(ref.watch(apiClientProvider)));

String _friendly(Object e) => e is ApiException
    ? e.message
    : 'Error inesperado. Intenta de nuevo.';

String _mimeFor(String path) {
  final ext = path.split('.').last.toLowerCase();
  return switch (ext) {
    'pdf' => 'application/pdf',
    'txt' => 'text/plain',
    'png' => 'image/png',
    'webp' => 'image/webp',
    'zip' => 'application/zip',
    _ => 'image/jpeg',
  };
}

class KnowledgeScreen extends ConsumerStatefulWidget {
  const KnowledgeScreen({super.key});

  @override
  ConsumerState<KnowledgeScreen> createState() => _KnowledgeScreenState();
}

class _KnowledgeScreenState extends ConsumerState<KnowledgeScreen> {
  List<KnowledgeAsset> _docs = [];
  bool _loading = true;
  bool _uploading = false;
  String? _error;
  String? _notice;

  @override
  void initState() {
    super.initState();
    Future.microtask(_load);
  }

  Future<void> _load() async {
    try {
      final docs =
          await ref.read(knowledgeRepositoryProvider).listDocuments();
      if (mounted) {
        setState(() {
          _docs = docs;
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

  Future<void> _pickAndUpload() async {
    final files = await FilePicker.pickFiles(
      type: FileType.custom,
      allowedExtensions: const ['pdf', 'txt', 'jpg', 'jpeg', 'png', 'webp', 'zip'],
    );
    if (files.isEmpty) return;
    final file = files.first;
    final bytes = await file.readAsBytes();
    if (bytes.isEmpty) return;
    setState(() {
      _uploading = true;
      _error = null;
      _notice = null;
    });
    try {
      final repo = ref.read(knowledgeRepositoryProvider);
      final kind =
          file.extension == 'pdf' || file.extension == 'txt'
              ? 'documents'
              : 'images';
      final mime = _mimeFor(file.name);
      final req = await repo.requestUpload(kind,
          filename: file.name, contentType: mime, fileSize: bytes.length);
      await repo.putFile(req['presigned_url'] as String, bytes,
          contentType: mime);
      final done = await repo.confirm(
          '${req['record_id']}', kind == 'documents' ? 'document' : 'image');
      if (mounted) {
        setState(() {
          _notice = 'Adjuntado: ${done.status}. Se indexará en segundo plano.';
        });
      }
      await _load();
    } catch (e) {
      if (mounted) setState(() => _error = _friendly(e));
    } finally {
      if (mounted) setState(() => _uploading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return SafeArea(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            FilledButton.icon(
              style: FilledButton.styleFrom(
                  minimumSize: const Size(double.infinity, 48)),
              onPressed: _uploading ? null : _pickAndUpload,
              icon: const Icon(Icons.upload_file),
              label: const Text('Adjuntar documento/imagen'),
            ),
            if (_uploading) ...[
              const SizedBox(height: 8),
              const LinearProgressIndicator(),
            ],
            if (_notice != null) ...[
              const SizedBox(height: 8),
              Text(_notice!),
            ],
            if (_error != null) ...[
              const SizedBox(height: 8),
              Semantics(
                liveRegion: true,
                child: Text(_error!,
                    style: TextStyle(
                        color: Theme.of(context).colorScheme.error)),
              ),
            ],
            const SizedBox(height: 8),
            Expanded(
              child: _loading
                  ? const Center(child: CircularProgressIndicator())
                  : _docs.isEmpty
                      ? const Center(
                          child: Text('Sin documentos todavía.'))
                      : RefreshIndicator(
                          onRefresh: _load,
                          child: ListView.builder(
                            itemCount: _docs.length,
                            itemBuilder: (context, i) {
                              final d = _docs[i];
                              return Card(
                                child: ListTile(
                                  leading: const Icon(
                                      Icons.description_outlined),
                                  title: Text(d.recordId.length > 13
                                      ? '${d.recordId.substring(0, 13)}…'
                                      : d.recordId),
                                  subtitle:
                                      Text('Estado: ${d.status}'),
                                  trailing: d.fileSize != null
                                      ? Text(
                                          '${(d.fileSize! / 1024).toStringAsFixed(0)} KB')
                                      : null,
                                ),
                              );
                            },
                          ),
                        ),
            ),
          ],
        ),
      ),
    );
  }
}
