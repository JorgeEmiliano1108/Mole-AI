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
      SystemMetrics.fromJson(await _api.getJson('admin/statistics'));

  Future<List<Map<String, dynamic>>> liveAlerts() async {
    final body = await _api.getJson('admin/live-alerts');
    return ((body['alerts'] as List?) ?? const [])
        .whereType<Map<String, dynamic>>()
        .toList();
  }

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
      if (role != null) 'role': role,
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
