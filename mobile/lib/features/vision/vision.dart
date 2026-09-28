/// Diagnóstico por foto, vía async congelada (contrato §5):
///
/// `POST diagnostics/` (multipart, timeout IA 120s) → `202 {task_id}` →
/// poll `GET ai/vision/status/<id>/` con backoff → `result.diagnosis`.
/// Fallo MS1 (NVIDIA caído): `status:failure + error` → se muestra, no se reintenta.
library;

import 'dart:io';

import 'package:dio/dio.dart';
import 'package:mole_ai/core/api_client.dart';
import 'package:mole_ai/core/errors.dart';
import 'package:mole_ai/core/offline_store.dart';

class Diagnosis {
  Diagnosis(
      {this.speciesCommon,
      this.speciesScientific,
      this.growthStage,
      this.afflictionName,
      this.afflictionType,
      this.severity,
      this.confidence,
      this.phPredicted,
      this.immediateActions = const [],
      this.disclaimer});

  factory Diagnosis.fromJson(Map<String, dynamic> j) => Diagnosis(
        speciesCommon: j['species_common'] as String?,
        speciesScientific: j['species_scientific'] as String?,
        growthStage: j['growth_stage'] as String?,
        afflictionName: j['affliction_name'] as String?,
        afflictionType: j['affliction_type'] as String?,
        severity: j['severity'] as String?,
        confidence: (j['confidence'] as num?)?.toDouble(),
        phPredicted: (j['ph_predicted'] as num?)?.toDouble(),
        immediateActions:
            ((j['immediate_actions'] as List?) ?? const []).whereType<String>().toList(),
        disclaimer: j['disclaimer'] as String?,
      );

  final String? speciesCommon;
  final String? speciesScientific;
  final String? growthStage;
  final String? afflictionName;
  final String? afflictionType;
  final String? severity;
  final double? confidence;
  final double? phPredicted;
  final List<String> immediateActions;
  final String? disclaimer;
}

class VisionStatus {
  VisionStatus({
    required this.status,
    this.state,
    this.diagnosis,
    this.error,
    this.info,
    this.isSafetyBlocked = false,
    this.safetyCode,
    this.safetyReason,
  });

  factory VisionStatus.fromJson(Map<String, dynamic> j) {
    final result = j['result'];
    Map<String, dynamic>? diagJson;
    bool blocked = false;
    String? safetyCode;
    String? safetyReason;
    if (result is Map<String, dynamic>) {
      blocked = result['blocked'] == true;
      final sb = result['safety_block'];
      if (sb is Map<String, dynamic>) {
        safetyCode = sb['code']?.toString();
        safetyReason = sb['reason']?.toString();
      }
      final d = result['diagnosis'];
      if (d is Map<String, dynamic>) diagJson = d;
    }
    return VisionStatus(
      status: '${j['status']}',
      state: j['state'] as String?,
      diagnosis: diagJson != null ? Diagnosis.fromJson(diagJson) : null,
      error: j['error']?.toString(),
      info: j['info']?.toString(),
      isSafetyBlocked: blocked,
      safetyCode: safetyCode,
      safetyReason: safetyReason,
    );
  }

  final String status; // pending|success|failure
  final String? state;
  final Diagnosis? diagnosis;
  final String? error;
  final String? info;
  final bool isSafetyBlocked;
  final String? safetyCode;
  final String? safetyReason;

  bool get isPending => status == 'pending';
  bool get isSuccess => status == 'success' && !isSafetyBlocked;
  bool get isFailure => status == 'failure' || isSafetyBlocked;
}

class VisionRepository {
  VisionRepository(this._api, {Future<void> Function(Duration)? delay})
      : _delay = delay ?? Future.delayed;

  final ApiClient _api;
  final Future<void> Function(Duration) _delay;

  /// Sube la foto. Retorna el `task_id` (202).
  /// `modelType`: disease_detection|plant_identification|pest_detection|
  /// nutrient_deficiency|growth_stage.
  Future<String> submitDiagnosis(List<int> imageBytes, String filename,
      {String? plantId, String modelType = 'disease_detection'}) async {
    final form = FormData.fromMap({
      'image': MultipartFile.fromBytes(imageBytes, filename: filename),
      'model_type': modelType,
      // No existe entrada null-aware en mapas; el patrón `case final p?`
      // es la forma moderna equivalente.
      // ignore: use_null_aware_elements
      if (plantId case final p?) 'plant_id': p,
    });
    final body = await _api.postMultipart('diagnostics/', form);
    final taskId = body['task_id']?.toString();
    if (taskId == null || taskId.isEmpty) {
      throw ApiException('El servidor no devolvió task_id.', details: body);
    }
    return taskId;
  }

  /// Poll con backoff (2s,4s,8s… máx 30s entre intentos, máx 10 intentos).
  /// Nunca busy-loop; 429 del throttle aborta con [RateLimitedException].
  Future<VisionStatus> pollStatus(String taskId,
      {int maxTries = 10}) async {
    var wait = const Duration(seconds: 2);
    VisionStatus last = VisionStatus(status: 'pending');
    for (var i = 0; i < maxTries; i++) {
      last = VisionStatus.fromJson(
          await _api.getJson('ai/vision/status/$taskId/'));
      if (!last.isPending) return last;
      await _delay(wait);
      final next = wait.inSeconds * 2;
      wait = Duration(seconds: next > 30 ? 30 : next);
    }
    return last;
  }

  Future<List<Map<String, dynamic>>> history({int limit = 20}) async {
    final body =
        await _api.getJson('diagnostics/history/', query: {'limit': '$limit'});
    return ((body['results'] as List?) ?? const [])
        .whereType<Map<String, dynamic>>()
        .toList();
  }

  /// Vacía la cola offline: sube cada pendiente (202 = aceptado → se elimina).
  /// Ante fallo de conexión se detiene (el resto espera a la próxima red).
  /// Ante error definitivo se cuenta intento y a los 5 se descarta.
  /// Retorna cuántos se subieron.
  Future<int> drainQueue(OfflineStore store) async {
    var done = 0;
    for (final item in await store.pending()) {
      final id = '${item['id']}';
      try {
        final bytes = await File('${item['path']}').readAsBytes();
        await submitDiagnosis(bytes, '${item['filename'] ?? 'foto.jpg'}',
            plantId: item['plant_id'] as String?,
            modelType: '${item['model_type'] ?? 'disease_detection'}');
        await store.remove(id);
        done++;
      } on RetryableException {
        break;
      } catch (_) {
        final cur = (item['tries'] as int?) ?? 0;
        if (cur + 1 >= 5) {
          await store.remove(id);
        } else {
          await store.bumpTries(id);
        }
      }
    }
    return done;
  }
}
