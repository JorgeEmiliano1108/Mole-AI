/// Reportes PDF vía MS3 (contrato §6, fase 2).
///
/// MS3 sirve `/api/v1/reports/*` (prefijo coherente con nginx + proxy Django,
/// `mole_report/app/main.py`): `POST generate` (exacta, sin `/`) →
/// `{job_id,status:QUEUED}` → poll `GET {job}/status` hasta `SUCCESS` →
/// `GET {job}/download` → `{download_url}` presigned (se abre externo:
/// sin permiso de almacenamiento en v1).
library;

import 'package:mole_ai/core/api_client.dart';
import 'package:mole_ai/core/errors.dart';

class ReportRepository {
  ReportRepository(this._api, {Future<void> Function(Duration)? delay})
      : _delay = delay ?? Future.delayed;

  final ApiClient _api;
  final Future<void> Function(Duration) _delay;

  /// Genera el reporte. `dateRangeDays` 30|60|90; `sensors` opcional.
  Future<String> generate({int dateRangeDays = 90, List<String> sensors = const []}) async {
    final body = await _api.postJson(
      'reports/generate',
      data: {'date_range_days': dateRangeDays, 'sensors': sensors},
      enforceSlash: false,
    );
    final jobId = body['job_id']?.toString();
    if (jobId == null || jobId.isEmpty) {
      throw ApiException('El servidor no devolvió job_id.', details: body);
    }
    return jobId;
  }

  /// Poll hasta SUCCESS (2s,4s,… máx 30s, máx 12 intentos ≈ 3 min).
  /// FAILURE/FAILED/ERROR → [ApiException] con el error del job.
  Future<Map<String, dynamic>> pollStatus(String jobId,
      {int maxTries = 12}) async {
    var wait = const Duration(seconds: 2);
    Map<String, dynamic> last = {'status': 'QUEUED'};
    for (var i = 0; i < maxTries; i++) {
      last = await _api.getJson('reports/$jobId/status', enforceSlash: false);
      final st = '${last['status'] ?? ''}'.toUpperCase();
      if (st == 'SUCCESS') return last;
      if (st == 'FAILURE' || st == 'FAILED' || st == 'ERROR') {
        throw ApiException(
            'El reporte falló: ${last['error'] ?? st}', details: last);
      }
      await _delay(wait);
      final next = wait.inSeconds * 2;
      wait = Duration(seconds: next > 30 ? 30 : next);
    }
    throw RetryableException(
        'El reporte sigue en proceso. Intenta de nuevo en un momento.');
  }

  /// URL presigned de descarga (válida ~24h; el backend la regenera si expiró).
  Future<String> downloadUrl(String jobId) async {
    final body = await _api.getJson('reports/$jobId/download',
        enforceSlash: false);
    final url = body['download_url']?.toString();
    if (url == null || !url.startsWith('http')) {
      throw ApiException('Reporte aún no listo.', details: body);
    }
    return url;
  }
}
