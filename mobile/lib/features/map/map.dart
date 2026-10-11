/// Mapa de hotspots + clima (contrato §6, fase 2).
///
/// Mismos datos que la web (Leaflet→flutter_map): tiles CartoDB dark,
/// `GET map/hotspots/` (JWT) y `GET weather/current/` (público).
/// Sin mi-ubicación en v1 (sin permiso LOCATION).
library;

import 'package:mole_ai/core/api_client.dart';
import 'package:mole_ai/core/errors.dart';

class Hotspot {
  Hotspot(
      {required this.lat,
      required this.lng,
      required this.severity,
      this.species});

  factory Hotspot.fromJson(Map<String, dynamic> j) {
    final h = Hotspot.tryParse(j);
    if (h == null) {
      throw ApiException('Hotspot inválido.', details: j);
    }
    return h;
  }

  /// F1: `lat/lng` ausentes o no numéricos → null (la lista los salta)
  /// en vez de reventar todo el mapa con `TypeError`.
  static Hotspot? tryParse(Map<String, dynamic> j) {
    final lat = j['lat'];
    final lng = j['lng'];
    if (lat is! num || lng is! num) return null;
    return Hotspot(
      lat: lat.toDouble(),
      lng: lng.toDouble(),
      severity: '${j['severity']}',
      species: j['species'] as String?,
    );
  }

  final double lat;
  final double lng;
  final String severity; // high|medium|low
  final String? species;
}

class CurrentWeather {
  CurrentWeather({this.temp, this.humidity, this.description});

  factory CurrentWeather.fromJson(Map<String, dynamic> j) {
    final main = j['main'];
    final weather = j['weather'];
    String? desc;
    if (weather is List && weather.isNotEmpty) {
      final w0 = weather.first;
      if (w0 is Map) desc = w0['description'] as String?;
    }
    return CurrentWeather(
      temp: main is Map ? (main['temp'] as num?)?.toDouble() : null,
      humidity: main is Map ? (main['humidity'] as num?)?.toDouble() : null,
      description: desc,
    );
  }

  final double? temp;
  final double? humidity;
  final String? description;
}

class MapRepository {
  MapRepository(this._api);
  final ApiClient _api;

  Future<List<Hotspot>> hotspots() async {
    final body = await _api.getJson('map/hotspots/');
    // F1: entradas inválidas se saltan; un hotspot roto no tumba el mapa.
    return ((body['hotspots'] as List?) ?? const [])
        .whereType<Map<String, dynamic>>()
        .map(Hotspot.tryParse)
        .whereType<Hotspot>()
        .toList();
  }

  Future<CurrentWeather> currentWeather(double lat, double lon) async {
    final body = await _api
        .getJson('weather/current/', query: {'lat': '$lat', 'lon': '$lon'});
    return CurrentWeather.fromJson(body);
  }
}
