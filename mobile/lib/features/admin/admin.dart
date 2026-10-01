/// Repositorios de administración (issue 15, rol admin|superuser).
///
/// Métricas (admin/statistics + live-alerts), usuarios (CRUD admin) y base de
/// conocimiento (training/* presigned PUT + confirm + polling de estado).
library;

import 'package:dio/dio.dart';
import 'package:mole_ai/core/api_client.dart';

class SystemMetrics {
  SystemMetrics(
      {required this.users,
      required this.registrations,
      required this.health,
      required this.totalPlants});

  factory SystemMetrics.fromJson(Map<String, dynamic> j) => SystemMetrics(
        users: (j['users'] as List? ?? const []).map((e) => e is int ? e : int.tryParse('$e') ?? 0).toList(),
        registrations:
            (j['regs'] as List? ?? const []).map((e) => e is int ? e : int.tryParse('$e') ?? 0).toList(),
        health: (j['health'] as List? ?? const [])
            .map((e) => e is num ? e.toDouble() : double.tryParse('$e') ?? 0.0)
            .toList(),
        totalPlants: (j['total_plants'] as int?) ?? 0,
      );

  final List<int> users;
  final List<int> registrations;
  final List<double> health;
  final int totalPlants;
}

class ManagedUser {
  ManagedUser(
      {required this.id,
      required this.username,
      this.email,
      this.role,
      this.isActive = true});

  factory ManagedUser.fromJson(Map<String, dynamic> j) => ManagedUser(
        id: j['id'],
        username: '${j['username']}',
        email: j['email'] as String?,
        role: j['role'] as String?,
        isActive: j['is_active'] != false,
      );

  final dynamic id;
  final String username;
  final String? email;
  final String? role;
  final bool isActive;
}

/// Evento del centro de fallas (issue N-2): forma común de las 4 secciones.
class SystemEvent {
  SystemEvent(
      {required this.severity,
      required this.title,
      this.detail = '',
      this.deviceId = '',
      this.timestamp = ''});

  factory SystemEvent.security(Map<String, dynamic> j) => SystemEvent(
        severity: '${j['tipo'] ?? 'info'}',
        title: 'Seguridad: ${j['action'] ?? '?'} (usuario ${j['user_id'] ?? '?'})',
        timestamp: '${j['timestamp'] ?? ''}',
      );

  factory SystemEvent.device(Map<String, dynamic> j) => SystemEvent(
        severity: '${j['tipo'] ?? 'warn'}',
        title: '${j['msg'] ?? 'Nodo sin estado'}',
        detail: (j['last_seen'] as String?)?.isNotEmpty == true
            ? 'Último contacto: ${j['last_seen']}'
            : 'Sin contacto registrado',
        deviceId: '${j['device_id'] ?? ''}',
        timestamp: '${j['last_seen'] ?? ''}',
      );

  factory SystemEvent.telemetry(Map<String, dynamic> j) => SystemEvent(
        severity: '${j['tipo'] ?? 'info'}',
        title: '${j['msg'] ?? 'Telemetría'}',
        timestamp: '${j['recorded_at'] ?? ''}',
      );

  factory SystemEvent.service(Map<String, dynamic> j) => SystemEvent(
        severity: '${j['tipo'] ?? 'info'}',
        title: 'Servicio ${j['service'] ?? '?'}: ${j['status'] ?? '?'}',
        detail: '${j['msg'] ?? ''}',
      );

  final String severity; // info|warn|error|critical
  final String title;
  final String detail;
  final String deviceId;
  final String timestamp;

  bool get isError => severity == 'error' || severity == 'critical';
  bool get isWarn => severity == 'warn';
}

class SystemEvents {
  SystemEvents(
      {this.security = const [],
      this.devices = const [],
      this.telemetry = const [],
      this.services = const []});

  factory SystemEvents.fromJson(Map<String, dynamic> j) {
    List<Map<String, dynamic>> sec(String k) =>
        ((j[k] as List?) ?? const []).whereType<Map<String, dynamic>>().toList();
    return SystemEvents(
      security: [for (final e in sec('security')) SystemEvent.security(e)],
      devices: [for (final e in sec('devices')) SystemEvent.device(e)],
      telemetry: [for (final e in sec('telemetry')) SystemEvent.telemetry(e)],
      services: [for (final e in sec('services')) SystemEvent.service(e)],
    );
  }

  final List<SystemEvent> security;
  final List<SystemEvent> devices;
  final List<SystemEvent> telemetry;
  final List<SystemEvent> services;

  int get errorCount =>
      [...security, ...devices, ...telemetry, ...services].where((e) => e.isError).length;
  int get warnCount =>
      [...security, ...devices, ...telemetry, ...services].where((e) => e.isWarn).length;
}

class ManagedDevice {
  ManagedDevice(
      {required this.id,
      required this.name,
      this.status = 'unknown',
      this.lastSeen = '',
      this.owner = ''});

  factory ManagedDevice.fromJson(Map<String, dynamic> j) => ManagedDevice(
        id: '${j['id'] ?? ''}',
        name: '${j['name'] ?? 'Sin nombre'}',
        status: '${j['status'] ?? 'unknown'}',
        lastSeen: '${j['last_seen'] ?? ''}',
        owner: '${j['owner'] ?? ''}',
      );

  final String id;
  final String name;
  final String status;
  final String lastSeen;
  final String owner;
}

class AuditEntry {
  AuditEntry(
      {this.id = 0,
      required this.action,
      this.userId,
      this.ipAddress = '',
      this.details = '',
      this.timestamp = ''});

  factory AuditEntry.fromJson(Map<String, dynamic> j) => AuditEntry(
        id: (j['id'] as num?)?.toInt() ?? 0,
        action: '${j['action'] ?? '?'}',
        userId: j['user_id'] is num ? (j['user_id'] as num).toInt() : null,
        ipAddress: '${j['ip_address'] ?? ''}',
        details: '${j['details'] ?? ''}',
        timestamp: '${j['timestamp'] ?? ''}',
      );

  final int id;
  final String action;
  final int? userId;
  final String ipAddress;
  final String details;
  final String timestamp;
}

class AuditPage {
  AuditPage({this.results = const [], this.count = 0});

  factory AuditPage.fromJson(Map<String, dynamic> j) => AuditPage(
        results: [for (final e in ((j['results'] as List?) ?? const [])) if (e is Map<String, dynamic>) AuditEntry.fromJson(e)],
        count: (j['count'] as num?)?.toInt() ?? 0,
      );

  final List<AuditEntry> results;
  final int count;
}

class KnowledgeAsset {
  KnowledgeAsset(
      {required this.recordId, required this.status, this.fileSize});

  factory KnowledgeAsset.fromJson(Map<String, dynamic> j) => KnowledgeAsset(
        recordId: '${j['record_id']}',
        status: '${j['status'] ?? 'unknown'}',
        fileSize: (j['file_size'] as num?)?.toInt(),
      );

  final String recordId;
  final String status;
  final int? fileSize;
}

class AdminRepository {
  AdminRepository(this._api);
  final ApiClient _api;

  Future<SystemMetrics> statistics() async =>
      SystemMetrics.fromJson(await _api.getJson('admin/statistics/'));

  Future<List<Map<String, dynamic>>> liveAlerts() async {
    final body = await _api.getJson('admin/live-alerts/');
    return ((body['alerts'] as List?) ?? const [])
        .whereType<Map<String, dynamic>>()
        .toList();
  }

  /// Centro de fallas (issue N-2): 4 secciones del backend.
  Future<SystemEvents> systemEvents() async =>
      SystemEvents.fromJson(await _api.getJson('admin/system-events/'));

  /// Flota para el portal (issue N-2). Sin tokens (el backend no los expone).
  Future<List<ManagedDevice>> devices() async {
    final body = await _api.getJson('admin/devices/');
    final list = body is List ? body : body['results'];
    if (list is! List) return [];
    return list.whereType<Map<String, dynamic>>().map(ManagedDevice.fromJson).toList();
  }

  /// Auditoría paginada con filtros (issue N-2).
  Future<AuditPage> auditLog({String? action, String? userId}) async =>
      AuditPage.fromJson(await _api.getJson('admin/audit-log/', query: {
        if (action?.isNotEmpty == true) 'action': action!,
        if (userId?.isNotEmpty == true) 'user_id': userId!,
      }));

  Future<List<ManagedUser>> users({String? search, String? role}) async {
    final q = search?.trim();
    final r = role?.trim();
    final body = await _api.getJson('admin/users/', query: {
      if (q?.isNotEmpty == true) 'search': q!,
      if (r?.isNotEmpty == true) 'role': r!,
    });
    return ((body['results'] as List?) ?? const [])
        .whereType<Map<String, dynamic>>()
        .map(ManagedUser.fromJson)
        .toList();
  }

  /// PATCH de rol/estado. El backend responde `{status, role, is_active}`
  /// (sin username/email): se reconstruye un [ManagedUser] profundo con
  /// fallback determinista `user-<id>` para que la UI nunca reciba `''`.
  Future<ManagedUser> updateUser(dynamic id,
      {String? role, bool? isActive}) async {
    final body = await _api.patchJson('admin/users/$id/', data: {
      // ignore: use_null_aware_elements
      if (role != null) 'role': role,
      // ignore: use_null_aware_elements
      if (isActive != null) 'is_active': isActive,
    });
    return ManagedUser.fromJson(<String, dynamic>{
      'id': id,
      'username': (body['username'] as String?) ?? 'user-$id',
      'email': body['email'] as String?,
      'role': (body['role'] as String?) ?? role,
      'is_active': body['is_active'] ?? isActive ?? true,
    });
  }
}

class KnowledgeRepository {
  KnowledgeRepository(this._api, {Dio? dio}) : _dio = dio ?? Dio();
  final ApiClient _api;
  final Dio _dio;

  /// Paso 1: pide URL presignada PUT (900s). `kind`: document|image.
  Future<Map<String, dynamic>> requestUpload(String kind,
      {required String filename,
      required String contentType,
      required int fileSize,
      String? category}) async {
    return _api.postJson('training/$kind/upload/request/', data: {
      'original_name': filename,
      'content_type': contentType,
      'file_size': fileSize,
      // ignore: use_null_aware_elements
      if (category != null) 'category': category,
    });
  }

  /// Paso 2: PUT directo a MinIO/S3 con Content-Type exacto.
  Future<void> putFile(String presignedUrl, List<int> bytes,
      {required String contentType}) async {
    await _dio.putUri(
      Uri.parse(presignedUrl),
      data: Stream.fromIterable([bytes]),
      options: Options(
        headers: {'Content-Type': contentType},
        contentType: contentType,
      ),
    );
  }

  /// Paso 3: confirma (verifica HEAD + encola indexado).
  Future<KnowledgeAsset> confirm(String recordId, String assetType) async {
    final body = await _api.postJson('training/upload/confirm/', data: {
      'record_id': recordId,
      'asset_type': assetType,
    });
    return KnowledgeAsset.fromJson(body);
  }

  Future<List<KnowledgeAsset>> listDocuments() async {
    final body = await _api.getJson('training/documents/');
    return ((body['results'] as List?) ?? const [])
        .whereType<Map<String, dynamic>>()
        .map(KnowledgeAsset.fromJson)
        .toList();
  }
}
