/// Persistencia offline (MRF01/MRNF02): caché JSON con TTL + cola de fotos.
///
/// F1: respaldo SQLite (`OfflineDb`: `telemetry_cache`, `diag_queue`) en vez
/// de SharedPreferences. La API pública no cambia: repos y pantallas intactos.
/// Etapa dev sin usuarios en prod: sin migración de las keys viejas de prefs
/// (instalación fresca parte de DB vacía).
/// Nada sensible: sin JWT, sin PII (solo lecturas cacheadas).
library;

import 'dart:convert';
import 'dart:io';

import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:path_provider/path_provider.dart';

import 'package:mole_ai/core/offline_db.dart';

/// Provider async: resuelve documents dir una sola vez.
final offlineStoreProvider = FutureProvider<OfflineStore>((_) async {
  final docs = await getApplicationDocumentsDirectory();
  return OfflineStore(
      db: SqfliteOfflineDb(docs.path), filesDir: docs.path);
});

/// Entrada de caché con timestamp.
class CacheEntry {
  CacheEntry({required this.cachedAt, required this.payload});
  final DateTime cachedAt;
  final Object? payload;
}

class OfflineStore {
  OfflineStore._(this._db, this._filesDir);

  factory OfflineStore({OfflineDb? db, String? filesDir}) =>
      OfflineStore._(db, filesDir);

  final OfflineDb? _db;
  final String? _filesDir;

  static const _ttlSpecies = Duration(hours: 24);
  static const _ttlCollection = Duration(hours: 24);

  OfflineDb get _ready {
    final db = _db;
    if (db == null) throw StateError('OfflineStore sin OfflineDb');
    return db;
  }

  // ── Caché genérica ──────────────────────────────────────────────

  Future<void> put(String key, Object? payload) async {
    await _ready.putCache(key, DateTime.now().toUtc().toIso8601String(),
        jsonEncode(payload));
  }

  /// Retorna null si no hay caché o expiró (ttl==null → nunca expira:
  /// último dato conocido de telemetría).
  Future<CacheEntry?> get(String key, {Duration? ttl}) async {
    final hit = await _ready.getCache(key);
    if (hit == null) return null;
    try {
      final at = DateTime.parse(hit.cachedAtIso);
      if (ttl != null && DateTime.now().toUtc().difference(at) > ttl) {
        return null;
      }
      return CacheEntry(cachedAt: at, payload: jsonDecode(hit.payloadJson));
    } catch (_) {
      return null;
    }
  }

  static String speciesKey(String q) => 'mole_cache_species:$q';
  static String collectionKey() => 'mole_cache_collection';
  static String telemetryKey(String plantId) => 'mole_cache_tele:$plantId';

  static Duration get speciesTtl => _ttlSpecies;
  static Duration get collectionTtl => _ttlCollection;

  // ── Cola de diagnósticos ────────────────────────────────────────

  /// Encola una foto. Retorna el id del pendiente.
  Future<String> enqueueDiagnosis(List<int> bytes, String filename,
      {String? plantId, String modelType = 'disease_detection'}) async {
    final dir = _filesDir;
    if (dir == null) throw StateError('OfflineStore sin filesDir');
    final id = DateTime.now().toUtc().microsecondsSinceEpoch.toString();
    final path = '$dir/pending_$id.jpg';
    await File(path).writeAsBytes(bytes, flush: true);
    await _ready.insertQueue({
      'id': id,
      'path': path,
      'filename': filename,
      'plant_id': plantId,
      'model_type': modelType,
      'created_at': DateTime.now().toUtc().toIso8601String(),
      'tries': 0,
    });
    return id;
  }

  Future<List<Map<String, dynamic>>> pending() async {
    final rows = await _ready.listQueue();
    return rows
        .map((r) => {
              'id': '${r['id']}',
              'path': '${r['path']}',
              'filename': '${r['filename']}',
              'plant_id': r['plant_id']?.toString(),
              'model_type': '${r['model_type']}',
              'created_at': '${r['created_at']}',
              'tries': (r['tries'] as int?) ?? 0,
            })
        .toList();
  }

  Future<void> remove(String id) async {
    String? path;
    for (final e in await _ready.listQueue()) {
      if ('${e['id']}' == id) path = '${e['path']}';
    }
    await _ready.deleteQueue(id);
    if (path != null) {
      try {
        await File(path).delete();
      } catch (_) {}
    }
  }

  Future<void> bumpTries(String id) => _ready.bumpQueueTries(id);
}
