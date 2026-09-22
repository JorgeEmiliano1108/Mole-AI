/// Capa SQLite offline (MRF01): 2 tablas, sin ORM.
///
/// - `telemetry_cache(key, cached_at, payload)`: último dato conocido.
/// - `diag_queue(id, path, filename, plant_id, model_type, created_at, tries)`:
///   fotos pendientes de subida.
/// Diseño testeable: [OfflineDb] abstracto; [SqfliteOfflineDb] productivo;
/// [MemoryOfflineDb] para tests (sin platform channels).
library;

import 'package:path/path.dart' as p;
import 'package:sqflite/sqflite.dart';

/// Contrato de persistencia offline (inyectable).
abstract class OfflineDb {
  Future<void> putCache(String key, String cachedAtIso, String payloadJson);
  Future<({String cachedAtIso, String payloadJson})?> getCache(String key);
  Future<List<Map<String, Object?>>> listQueue();
  Future<void> insertQueue(Map<String, Object?> row);
  Future<void> deleteQueue(String id);
  Future<void> bumpQueueTries(String id);
}

/// SQLite real (`mole_offline.db` en documents).
class SqfliteOfflineDb implements OfflineDb {
  SqfliteOfflineDb(this._dirPath);

  final String _dirPath;
  Database? _db;

  Future<Database> get _ready async {
    final db = _db;
    if (db != null && db.isOpen) return db;
    final created = await openDatabase(
      p.join(_dirPath, 'mole_offline.db'),
      version: 1,
      onCreate: (d, _) async {
        await d.execute(
            'CREATE TABLE telemetry_cache(key TEXT PRIMARY KEY, cached_at TEXT NOT NULL, payload TEXT NOT NULL)');
        await d.execute(
            'CREATE TABLE diag_queue(id TEXT PRIMARY KEY, path TEXT NOT NULL, filename TEXT NOT NULL, plant_id TEXT, model_type TEXT NOT NULL, created_at TEXT NOT NULL, tries INTEGER NOT NULL DEFAULT 0)');
      },
    );
    _db = created;
    return created;
  }

  @override
  Future<void> putCache(
      String key, String cachedAtIso, String payloadJson) async {
    final db = await _ready;
    await db.insert(
      'telemetry_cache',
      {'key': key, 'cached_at': cachedAtIso, 'payload': payloadJson},
      conflictAlgorithm: ConflictAlgorithm.replace,
    );
  }

  @override
  Future<({String cachedAtIso, String payloadJson})?> getCache(
      String key) async {
    final db = await _ready;
    final rows = await db.query('telemetry_cache',
        columns: ['cached_at', 'payload'],
        where: 'key = ?',
        whereArgs: [key],
        limit: 1);
    if (rows.isEmpty) return null;
    return (
      cachedAtIso: rows.first['cached_at'] as String,
      payloadJson: rows.first['payload'] as String,
    );
  }

  @override
  Future<List<Map<String, Object?>>> listQueue() async {
    final db = await _ready;
    return db.query('diag_queue', orderBy: 'created_at ASC');
  }

  @override
  Future<void> insertQueue(Map<String, Object?> row) async {
    final db = await _ready;
    await db.insert('diag_queue', row,
        conflictAlgorithm: ConflictAlgorithm.replace);
  }

  @override
  Future<void> deleteQueue(String id) async {
    final db = await _ready;
    await db.delete('diag_queue', where: 'id = ?', whereArgs: [id]);
  }

  @override
  Future<void> bumpQueueTries(String id) async {
    final db = await _ready;
    await db.rawUpdate(
        'UPDATE diag_queue SET tries = tries + 1 WHERE id = ?', [id]);
  }
}

/// En memoria para tests (misma semántica, sin nativo).
class MemoryOfflineDb implements OfflineDb {
  final _cache = <String, ({String cachedAtIso, String payloadJson})>{};
  final _queue = <String, Map<String, Object?>>{};

  @override
  Future<void> putCache(
          String key, String cachedAtIso, String payloadJson) async =>
      _cache[key] = (cachedAtIso: cachedAtIso, payloadJson: payloadJson);

  @override
  Future<({String cachedAtIso, String payloadJson})?> getCache(
          String key) async =>
      _cache[key];

  @override
  Future<List<Map<String, Object?>>> listQueue() async {
    final rows = _queue.values.toList()
      ..sort((a, b) =>
          '${a['created_at']}'.compareTo('${b['created_at']}'));
    return rows.map((r) => Map<String, Object?>.from(r)).toList();
  }

  @override
  Future<void> insertQueue(Map<String, Object?> row) async =>
      _queue['${row['id']}'] = Map<String, Object?>.from(row);

  @override
  Future<void> deleteQueue(String id) async => _queue.remove(id);

  @override
  Future<void> bumpQueueTries(String id) async {
    final row = _queue[id];
    if (row != null) row['tries'] = ((row['tries'] as int?) ?? 0) + 1;
  }
}
