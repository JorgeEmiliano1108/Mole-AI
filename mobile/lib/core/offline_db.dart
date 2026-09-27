/// Capa SQLite offline (MRF01): 2 tablas, sin ORM.
///
/// - `telemetry_cache(key, cached_at, payload)`: último dato conocido.
/// - `diag_queue(id, path, filename, plant_id, model_type, created_at, tries)`:
///   fotos pendientes de subida.
///
/// S1 (MASVS-STORAGE): `mole_offline.db` va cifrado con SQLCipher (AES-256);
/// la contraseña vive en `flutter_secure_storage` (`mole_db_key`), nunca en
/// código ni prefs. Instalaciones con DB en plano migran con respaldo
/// (export → recrear cifrado → reimportar); si la migración falla, wipe
/// limpio documentado. Los JPGs quedan en dir privado + fuera de backup
/// (residual documentado: cifrado de ficheros en fase posterior).
///
/// Diseño testeable: [OfflineDb] abstracto; [SqfliteOfflineDb] productivo;
/// [MemoryOfflineDb] para tests (sin platform channels).
library;

import 'dart:convert';
import 'dart:io';
import 'dart:math';

import 'package:path/path.dart' as p;
import 'package:sqflite_sqlcipher/sqflite.dart';

/// Contrato de persistencia offline (inyectable).
abstract class OfflineDb {
  Future<void> putCache(String key, String cachedAtIso, String payloadJson);
  Future<({String cachedAtIso, String payloadJson})?> getCache(String key);
  Future<List<Map<String, Object?>>> listQueue();
  Future<void> insertQueue(Map<String, Object?> row);
  Future<void> deleteQueue(String id);
  Future<void> bumpQueueTries(String id);

  // Consejos offline por clase (PVU/S5)
  Future<void> putAdvice(String cls, String text, {int maxEntries = 50});
  Future<String?> getAdvice(String cls);
}

/// Genera una contraseña de 256 bits en base64 (para `mole_db_key`).
/// Función pura: testeable sin platform channels.
String generateDbPassword([Random? random]) {
  final r = random ?? Random.secure();
  final bytes = List<int>.generate(32, (_) => r.nextInt(256));
  return base64UrlEncode(bytes);
}

/// SQLite real cifrado (`mole_offline.db` en documents, SQLCipher AES-256).
class SqfliteOfflineDb implements OfflineDb {
  SqfliteOfflineDb(this._dirPath, {required this.password});

  final String _dirPath;

  /// Contraseña resuelta por el llamador (secure storage). Vacía = sin cifrar
  /// (solo tests locales; producción siempre la exige vía provider).
  final String password;
  Database? _db;

  static const _schema = [
    'CREATE TABLE telemetry_cache(key TEXT PRIMARY KEY, cached_at TEXT NOT NULL, payload TEXT NOT NULL)',
    'CREATE TABLE diag_queue(id TEXT PRIMARY KEY, path TEXT NOT NULL, filename TEXT NOT NULL, plant_id TEXT, model_type TEXT NOT NULL, pvu_reason TEXT, created_at TEXT NOT NULL, tries INTEGER NOT NULL DEFAULT 0)',
    'CREATE TABLE offline_advice(class TEXT PRIMARY KEY, text TEXT NOT NULL, used_at TEXT NOT NULL)',
  ];

  Future<Database> _openEncrypted(String path) => openDatabase(
        path,
        password: password,
        version: 1,
        onCreate: (d, _) async {
          for (final ddl in _schema) {
            await d.execute(ddl);
          }
        },
      );

  static bool _isPlainDatabase(DatabaseException e) =>
      isNotADatabaseMessage(e.toString());

  /// Predicado puro (testeable): SQLCipher reporta así un fichero en plano.
  static bool isNotADatabaseMessage(String message) =>
      message.contains('not a database');

  /// Migración plano→cifrado con respaldo: exporta filas, borra el fichero,
  /// recrea cifrado y reimporta. Si algo falla, wipe limpio (documentado).
  Future<void> _migratePlainToEncrypted(String path) async {
    final plain = await openDatabase(path, version: 1);
    List<Map<String, Object?>> cache = [];
    List<Map<String, Object?>> queue = [];
    try {
      cache = await plain.query('telemetry_cache');
      queue = await plain.query('diag_queue');
    } finally {
      await plain.close();
    }
    await File(path).delete();
    final fresh = await _openEncrypted(path);
    try {
      for (final row in cache) {
        await fresh.insert('telemetry_cache', Map<String, Object?>.from(row),
            conflictAlgorithm: ConflictAlgorithm.replace);
      }
      for (final row in queue) {
        // Las rutas de JPG migran tal cual (residual: ficheros en claro).
        await fresh.insert('diag_queue', Map<String, Object?>.from(row),
            conflictAlgorithm: ConflictAlgorithm.replace);
      }
    } catch (_) {
      await fresh.close();
      await File(path).delete();
      rethrow;
    }
    await fresh.close();
  }

  Future<Database> get _ready async {
    final db = _db;
    if (db != null && db.isOpen) return db;
    final path = p.join(_dirPath, 'mole_offline.db');
    try {
      _db = await _openEncrypted(path);
    } on DatabaseException catch (e) {
      if (!_isPlainDatabase(e)) rethrow;
      await _migratePlainToEncrypted(path);
      _db = await _openEncrypted(path);
    }
    return _db!;
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

  @override
  Future<void> putAdvice(String cls, String text,
      {int maxEntries = 50}) async {
    final db = await _ready;
    final now = DateTime.now().toUtc().toIso8601String();
    await db.insert(
      'offline_advice',
      {'class': cls, 'text': text, 'used_at': now},
      conflictAlgorithm: ConflictAlgorithm.replace,
    );
    final count = (await db.rawQuery('SELECT COUNT(*) AS c FROM offline_advice'))
        .first['c'] as int;
    if (count > maxEntries) {
      final toDrop = count - maxEntries;
      await db.rawDelete(
        'DELETE FROM offline_advice WHERE rowid IN (SELECT rowid FROM offline_advice ORDER BY used_at ASC LIMIT ?)',
        [toDrop],
      );
    }
  }

  @override
  Future<String?> getAdvice(String cls) async {
    final db = await _ready;
    final rows = await db.query('offline_advice',
        columns: ['text'], where: 'class = ?', whereArgs: [cls], limit: 1);
    if (rows.isEmpty) return null;
    await db.update(
      'offline_advice',
      {'used_at': DateTime.now().toUtc().toIso8601String()},
      where: 'class = ?',
      whereArgs: [cls],
    );
    return rows.first['text'] as String?;
  }
}

/// En memoria para tests (misma semántica, sin nativo).
class MemoryOfflineDb implements OfflineDb {
  final _cache = <String, ({String cachedAtIso, String payloadJson})>{};
  final _queue = <String, Map<String, Object?>>{};
  final _advice = <String, ({String text, DateTime usedAt})>{};

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

  @override
  Future<void> putAdvice(String cls, String text,
      {int maxEntries = 50}) async {
    _advice[cls] = (text: text, usedAt: DateTime.now().toUtc());
    if (_advice.length > maxEntries) {
      final sorted = _advice.entries.toList()
        ..sort((a, b) => a.value.usedAt.compareTo(b.value.usedAt));
      for (final e in sorted.take(_advice.length - maxEntries)) {
        _advice.remove(e.key);
      }
    }
  }

  @override
  Future<String?> getAdvice(String cls) async {
    final entry = _advice[cls];
    if (entry == null) return null;
    _advice[cls] = (text: entry.text, usedAt: DateTime.now().toUtc());
    return entry.text;
  }
}
