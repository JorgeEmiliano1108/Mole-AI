/// Pantalla de reportes PDF (contrato §6): generar → esperar → abrir.
library;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:mole_ai/core/errors.dart';
import 'package:mole_ai/features/auth/auth_controller.dart';
import 'package:mole_ai/features/reports/reports.dart';
import 'package:url_launcher/url_launcher.dart';

final reportRepositoryProvider = Provider<ReportRepository>(
    (ref) => ReportRepository(ref.watch(apiClientProvider)));

String _friendly(Object e) => e is ApiException
    ? e.message
    : 'Error inesperado. Intenta de nuevo.';

class ReportsScreen extends ConsumerStatefulWidget {
  const ReportsScreen({super.key});

  @override
  ConsumerState<ReportsScreen> createState() => _ReportsScreenState();
}

class _ReportsScreenState extends ConsumerState<ReportsScreen> {
  int _days = 30;
  String? _phase; // working|done|error
  String? _message;
  String? _url;

  Future<void> _generate() async {
    setState(() {
      _phase = 'working';
      _message = 'Generando reporte…';
      _url = null;
    });
    try {
      final repo = ref.read(reportRepositoryProvider);
      final jobId = await repo.generate(dateRangeDays: _days);
      if (!mounted) return;
      setState(() => _message = 'Procesando en el servidor…');
      await repo.pollStatus(jobId);
      final url = await repo.downloadUrl(jobId);
      if (!mounted) return;
      setState(() {
        _phase = 'done';
        _message = null;
        _url = url;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _phase = 'error';
        _message = _friendly(e);
      });
    }
  }

  Future<void> _open() async {
    final url = _url;
    if (url == null) return;
    final uri = Uri.tryParse(url);
    if (uri == null) return;
    await launchUrl(uri, mode: LaunchMode.externalApplication);
  }

  @override
  Widget build(BuildContext context) {
    const options = [30, 60, 90];
    return SafeArea(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            const Text('Rango del reporte:'),
            const SizedBox(height: 8),
            SegmentedButton<int>(
              segments: [
                for (final d in options)
                  ButtonSegment(value: d, label: Text('$d días')),
              ],
              selected: {_days},
              onSelectionChanged: _phase == 'working'
                  ? null
                  : (s) => setState(() => _days = s.single),
            ),
            const SizedBox(height: 16),
            FilledButton(
              style: FilledButton.styleFrom(
                  minimumSize: const Size(double.infinity, 48)),
              onPressed: _phase == 'working' ? null : _generate,
              child: const Text('Generar PDF'),
            ),
            const SizedBox(height: 16),
            if (_phase == 'working')
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
                  onPressed: _generate, child: const Text('Reintentar')),
            ],
            if (_phase == 'done' && _url != null)
              FilledButton.tonalIcon(
                onPressed: _open,
                icon: const Icon(Icons.picture_as_pdf),
                label: const Text('Abrir PDF'),
              ),
          ],
        ),
      ),
    );
  }
}
