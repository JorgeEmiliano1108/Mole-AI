/// Modelos y repositorio de especies (contrato §2).
///
/// `GET plants/search/` es público y devuelve máx 50 resultados con
/// `protection_warning` cuando `is_protected_nom059` (NOM-059, obligatorio).
library;

import 'package:mole_ai/core/api_client.dart';
import 'package:mole_ai/core/errors.dart';
import 'package:mole_ai/core/offline_store.dart';

class Species {
  Species({
    required this.id,
    required this.nombre,
    required this.nombreCientifico,
    this.descripcion = '',
    this.category,
    this.humedad,
    this.temperatura,
    this.ph,
    this.imageUrl = '',
    this.isProtected = false,
    this.protectionWarning,
    this.protectionCategory,
    this.habitat,
    this.uses,
    this.isEndemic = false,
  });

  factory Species.fromJson(Map<String, dynamic> j) => Species(
        id: '${j['id']}',
        nombre: '${j['nombre'] ?? ''}',
        nombreCientifico: '${j['nombre_cientifico'] ?? ''}',
        descripcion: '${j['descripcion'] ?? ''}',
        category: j['category'] as String?,
        humedad: j['humedad'] as String?,
        temperatura: j['temperatura'] as String?,
        ph: j['ph'] as String?,
        imageUrl: '${j['image_url'] ?? ''}',
        isProtected: j['is_protected_nom059'] == true,
        protectionWarning: j['protection_warning'] as String?,
        protectionCategory: j['protection_category'] as String?,
        habitat: j['habitat'] as String?,
        uses: j['uses'] as String?,
        isEndemic: j['is_endemic'] == true,
      );

  final String id;
  final String nombre;
  final String nombreCientifico;
  final String descripcion;
  final String? category;
  final String? humedad;
  final String? temperatura;
  final String? ph;
  final String imageUrl;
  final bool isProtected;
  final String? protectionWarning;
  final String? protectionCategory;
  final String? habitat;
  final String? uses;
  final bool isEndemic;
}

class SpeciesRepository {
  SpeciesRepository(this._api);

  final ApiClient _api;

  /// Búsqueda pública. Exige `q` o `category` (400 del backend si vacías).
  Future<List<Species>> search(
      {String? q, String? category, bool? endemic, String? habitat}) async {
    final query = <String, dynamic>{
      if (q != null && q.trim().isNotEmpty) 'q': q.trim(),
      if (category != null && category.trim().isNotEmpty)
        'category': category.trim(),
      if (endemic == true) 'endemic': '1',
      if (habitat != null && habitat.trim().isNotEmpty)
        'habitat': habitat.trim(),
    };
    if (query.isEmpty) return [];
    // El backend devuelve array directo (sin envelope) en este endpoint.
    final list = await _api.getList('plants/search/', query: query);
    return _speciesList(list);
  }

  /// Con caché offline: si hay red guarda el resultado; si falla por
  /// conexión devuelve la caché (offline=true) o relanza el error.
  Future<({List<Species> results, bool offline})> searchCached(
      String q, OfflineStore store,
      {bool? endemic, String? habitat}) async {
    final key = OfflineStore.speciesKey(
        '${q.trim()}|e=${endemic == true}|h=${habitat ?? ''}');
    try {
      final results =
          await search(q: q, endemic: endemic, habitat: habitat);
      await store.put(
          key, results.map((s) => _toCacheJson(s)).toList());
      return (results: results, offline: false);
    } on RetryableException {
      final hit = await store.get(key, ttl: OfflineStore.speciesTtl);
      final raw = hit?.payload;
      if (raw is List) {
        return (
          results: raw
              .whereType<Map<String, dynamic>>()
              .map(Species.fromJson)
              .toList(),
          offline: true
        );
      }
      rethrow;
    }
  }

  /// Catálogo paginado `{count,next,previous,results}` (contrato §2, PAGE_SIZE 50).
  Future<({int count, List<Species> results, String? next})> page(
      {String? url}) async {
    final body = url != null
        ? await _api.getJson(_relative(url))
        : await _api.getJson('plants/species/');
    final results = _speciesList(body['results']);
    return (
      count: (body['count'] as int?) ?? results.length,
      results: results,
      next: body['next'] as String?,
    );
  }

  /// `next` absoluto del paginador → path relativo para el cliente.
  static String _relative(String url) {
    final i = url.indexOf('/api/v1/');
    return i >= 0 ? url.substring(i + '/api/v1/'.length) : url;
  }

  static List<Species> _speciesList(Object? raw) => (raw as List? ?? const [])
      .whereType<Map<String, dynamic>>()
      .map(Species.fromJson)
      .toList();

  /// Subconjunto serializable para la caché offline (re-parseable).
  static Map<String, dynamic> _toCacheJson(Species s) => {
        'id': s.id,
        'nombre': s.nombre,
        'nombre_cientifico': s.nombreCientifico,
        'descripcion': s.descripcion,
        'category': s.category,
        'humedad': s.humedad,
        'temperatura': s.temperatura,
        'ph': s.ph,
        'image_url': s.imageUrl,
        if (s.isProtected) 'is_protected_nom059': true,
        if (s.protectionWarning != null)
          'protection_warning': s.protectionWarning,
        if (s.protectionCategory != null)
          'protection_category': s.protectionCategory,
        if (s.habitat != null) 'habitat': s.habitat,
        if (s.uses != null) 'uses': s.uses,
        if (s.isEndemic) 'is_endemic': true,
      };
}
