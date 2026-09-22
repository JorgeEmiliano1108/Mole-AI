/// Modelos y repositorios de plantas y telemetría (contrato §3, §4).
///
/// Solo lectura (ADR-0002): el APK nunca publica telemetría.
/// `my-collection/` y `plants/search/` devuelven array directo;
/// `user-plants/` devuelve envelope `{results,count}`.
library;

import 'package:mole_ai/core/api_client.dart';
import 'package:mole_ai/core/errors.dart';
import 'package:mole_ai/core/offline_store.dart';

class Plant {
  Plant(
      {required this.id,
      required this.nickname,
      this.speciesId,
      this.createdAt});

  factory Plant.fromJson(Map<String, dynamic> j) => Plant(
        id: '${j['id']}',
        nickname: '${j['nickname'] ?? ''}',
        speciesId: j['species_id']?.toString(),
        createdAt: j['created_at'] as String?,
      );

  final String id;
  final String nickname;
  final String? speciesId;
  final String? createdAt;
}

class PlantsRepository {
  PlantsRepository(this._api);
  final ApiClient _api;

  /// Array directo `[{id,nickname,species_id?,created_at}]`.
  Future<List<Plant>> myCollection() async {
    final list = await _api.getList('user-plants/my-collection/');
    return list
        .whereType<Map<String, dynamic>>()
        .map(Plant.fromJson)
        .toList();
  }

  /// Envelope `{results:[…], count}`.
  Future<List<Plant>> listPlants() async {
    final body = await _api.getJson('user-plants/');
    return ((body['results'] as List?) ?? const [])
        .whereType<Map<String, dynamic>>()
        .map(Plant.fromJson)
        .toList();
  }

  Future<Plant> detail(String plantId) async =>
      Plant.fromJson(await _api.getJson('user-plants/$plantId/'));

  /// Con caché offline (TTL 24h).
  Future<({List<Plant> plants, bool offline})> myCollectionCached(
      OfflineStore store) async {
    final key = OfflineStore.collectionKey();
    try {
      final plants = await myCollection();
      await store.put(
          key,
          plants
              .map((p) => {
                    'id': p.id,
                    'nickname': p.nickname,
                    'species_id': p.speciesId,
                    'created_at': p.createdAt,
                  })
              .toList());
      return (plants: plants, offline: false);
    } on RetryableException {
      final hit =
          await store.get(key, ttl: OfflineStore.collectionTtl);
      final raw = hit?.payload;
      if (raw is List) {
        return (
          plants: raw
              .whereType<Map<String, dynamic>>()
              .map(Plant.fromJson)
              .toList(),
          offline: true
        );
      }
      rethrow;
    }
  }
}

class Telemetry {
  Telemetry(
      {required this.plantId,
      this.recordedAt,
      this.soilHumidity,
      this.airHumidity,
      this.airTemperature,
      this.uvIndex,
      this.phLevel});

  factory Telemetry.fromJson(Map<String, dynamic> j) => Telemetry(
        plantId: '${j['plant_id']}',
        recordedAt: j['recorded_at'] as String?,
        soilHumidity: (j['soil_humidity'] as num?)?.toDouble(),
        airHumidity: (j['air_humidity'] as num?)?.toDouble(),
        airTemperature: (j['air_temperature'] as num?)?.toDouble(),
        uvIndex: (j['uv_index'] as num?)?.toDouble(),
        phLevel: (j['ph_level'] as num?)?.toDouble(),
      );

  final String plantId;
  final String? recordedAt;
  final double? soilHumidity;
  final double? airHumidity;
  final double? airTemperature;
  final double? uvIndex;
  final double? phLevel;

  /// Sin `recorded_at` no hay dato (nodo sin logs): la UI muestra vacío,
  /// nunca inventa valores.
  bool get hasData => recordedAt != null;
}

class AmbientReading {
  AmbientReading(
      {this.airTemperature,
      this.airHumidity,
      this.uvIndex,
      this.lightLevel,
      this.recordedAt});

  factory AmbientReading.fromJson(Map<String, dynamic> j) => AmbientReading(
        airTemperature: (j['air_temperature'] as num?)?.toDouble(),
        airHumidity: (j['air_humidity'] as num?)?.toDouble(),
        uvIndex: (j['uv_index'] as num?)?.toDouble(),
        lightLevel: (j['light_level'] as num?)?.toDouble(),
        recordedAt: j['recorded_at'] as String?,
      );

  final double? airTemperature;
  final double? airHumidity;
  final double? uvIndex;
  final double? lightLevel;
  final String? recordedAt;
}

class SoilCell {
  SoilCell(
      {required this.pin,
      this.plantId,
      this.plantNickname,
      this.species,
      this.soilHumidity,
      this.recordedAt});

  factory SoilCell.fromJson(Map<String, dynamic> j) => SoilCell(
        pin: '${j['pin']}',
        plantId: j['plant_id']?.toString(),
        plantNickname: j['plant_nickname'] as String?,
        species: j['species'] as String?,
        soilHumidity: (j['soil_humidity'] as num?)?.toDouble(),
        recordedAt: j['recorded_at'] as String?,
      );

  final String pin;
  final String? plantId;
  final String? plantNickname;
  final String? species;
  final double? soilHumidity;
  final String? recordedAt;
}

class DeviceHealth {
  DeviceHealth(
      {required this.deviceId,
      this.deviceName,
      this.status,
      this.lastSeen,
      this.lastSeenDeltaSeconds,
      this.ambient,
      this.soil = const [],
      this.sreMetrics = const {}});

  factory DeviceHealth.fromJson(Map<String, dynamic> j) => DeviceHealth(
        deviceId: '${j['device_id']}',
        deviceName: j['device_name'] as String?,
        status: j['status'] as String?,
        lastSeen: j['last_seen'] as String?,
        lastSeenDeltaSeconds: j['last_seen_delta_seconds'] as int?,
        ambient: j['ambient'] is Map<String, dynamic>
            ? AmbientReading.fromJson(j['ambient'] as Map<String, dynamic>)
            : null,
        soil: ((j['soil'] as List?) ?? const [])
            .whereType<Map<String, dynamic>>()
            .map(SoilCell.fromJson)
            .toList(),
        sreMetrics: (j['sre_metrics'] as Map?) ?? const {},
      );

  final String deviceId;
  final String? deviceName;
  final String? status;
  final String? lastSeen;
  final int? lastSeenDeltaSeconds;
  final AmbientReading? ambient;
  final List<SoilCell> soil;
  final Map sreMetrics;
}

class TelemetryRepository {
  TelemetryRepository(this._api);
  final ApiClient _api;

  /// Última telemetría de una planta del usuario.
  /// 404 si es ajena o no tiene logs (la UI muestra "sin datos").
  Future<Telemetry> latest(String plantId) async => Telemetry.fromJson(
      await _api.getJson('telemetry/latest/', query: {'plant_id': plantId}));

  Future<DeviceHealth> deviceHealth(String deviceId) async =>
      DeviceHealth.fromJson(await _api.getJson('devices/$deviceId/health/'));

  /// Último dato conocido (sin TTL: un dato viejo etiquetado es mejor que
  /// nada en campo). Los 404 (sin logs) no se cachean.
  Future<({Telemetry? telemetry, bool offline})> latestCached(
      OfflineStore store, String plantId) async {
    final key = OfflineStore.telemetryKey(plantId);
    try {
      final t = await latest(plantId);
      await store.put(key, {
        'plant_id': t.plantId,
        'recorded_at': t.recordedAt,
        'soil_humidity': t.soilHumidity,
        'air_humidity': t.airHumidity,
        'air_temperature': t.airTemperature,
        'uv_index': t.uvIndex,
        'ph_level': t.phLevel,
      });
      return (telemetry: t, offline: false);
    } on RetryableException {
      final hit = await store.get(key);
      final raw = hit?.payload;
      if (raw is Map<String, dynamic>) {
        return (telemetry: Telemetry.fromJson(raw), offline: true);
      }
      rethrow;
    }
  }
}
