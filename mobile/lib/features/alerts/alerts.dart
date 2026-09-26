/// Avisos de plantas del usuario (issue N-1).
///
/// Fuente: `GET user-plants/my-alerts/` (scoped por propiedad, botánico y
/// admin). Parseo defensivo: nada truena ante backend degradado (issue 21).
library;

import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:mole_ai/core/api_client.dart';
import 'package:mole_ai/features/auth/auth_controller.dart';

/// Severidad tal como la emite el backend (`tipo`).
enum AlertSeverity { info, warn, error;

  static AlertSeverity parse(Object? v) => switch (v) {
        'error' => AlertSeverity.error,
        'warn' => AlertSeverity.warn,
        _ => AlertSeverity.info,
      };
}

class PlantAlert {
  PlantAlert(
      {required this.severity,
      required this.message,
      this.source = '',
      this.recordedAt = '',
      this.deviceId = '',
      this.plantId = ''});

  factory PlantAlert.fromJson(Map<String, dynamic> j) => PlantAlert(
        severity: AlertSeverity.parse(j['tipo']),
        message: '${j['msg'] ?? 'Aviso del sistema'}',
        source: '${j['source'] ?? ''}',
        recordedAt: '${j['recorded_at'] ?? ''}',
        deviceId: '${j['device_id'] ?? ''}',
        plantId: '${j['plant_id'] ?? ''}',
      );

  final AlertSeverity severity;
  final String message;
  final String source;
  final String recordedAt;
  final String deviceId;
  final String plantId;

  /// Solo error+warn escalan a notificación local (decisión N-1).
  bool get notifiable =>
      severity == AlertSeverity.error || severity == AlertSeverity.warn;

  /// Dedup estable entre sondeos (el backend no emite id).
  String get fingerprint =>
      '${severity.name}|$message|$recordedAt|$deviceId|$plantId|$source';
}

class AlertsRepository {
  AlertsRepository(this._api);
  final ApiClient _api;

  /// Lista de avisos (vacía si el backend responde forma inesperada).
  Future<List<PlantAlert>> myAlerts() async {
    final body = await _api.getJson('user-plants/my-alerts/');
    final list = body['alerts'];
    if (list is! List) return [];
    return [
      for (final e in list)
        if (e is Map<String, dynamic>) PlantAlert.fromJson(e)
    ];
  }
}

final alertsRepositoryProvider = Provider<AlertsRepository>(
    (ref) => AlertsRepository(ref.watch(apiClientProvider)));

/// No-leídos para el badge del drawer (se resetea al abrir Mis avisos).
class UnreadAlerts extends Notifier<int> {
  @override
  int build() => 0;

  void reset() => state = 0;
  void add(int n) => state = state + n;
}

final unreadAlertsProvider =
    NotifierProvider<UnreadAlerts, int>(UnreadAlerts.new);
