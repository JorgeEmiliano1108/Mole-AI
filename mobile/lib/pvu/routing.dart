/// PVU — Predictive Vehicle Unit? Actually Predictive routing Unit (conmutación predictiva).
///
/// Módulo puro de decisión: elige la ruta de inferencia ANTES de gastar
/// batería o RAM. No depende de red ni de modelo; se testea en host.
library;

/// Estado de conectividad canónico.
enum ConnectivityStatus { online, metered, offline }

/// Muestra opcional de señal Wi-Fi.
class RssiSample {
  const RssiSample(this.rssi);
  final int rssi;
}

/// Resultado de la conmutación predictiva.
sealed class PvuRoute {
  const PvuRoute({required this.reason});
  final String reason;
  String get endpoint;
}

/// Inferencia 100% local (edge). Sin consumo de datos, baja latencia.
class LocalRoute extends PvuRoute {
  const LocalRoute({required super.reason});
  @override
  String get endpoint => 'edge';
}

/// Inferencia 100% en la nube. Se usa cuando el edge no es viable.
class CloudRoute extends PvuRoute {
  const CloudRoute({required super.reason});
  @override
  String get endpoint => 'cloud';
}

/// Edge primero; si la confianza es baja, fallback a la nube.
class HybridRoute extends PvuRoute {
  const HybridRoute({super.reason = 'default'});
  @override
  String get endpoint => 'edge_then_cloud';
}

/// Decide la ruta PVU en menos de 2 ms (garantía <2 s con Stopwatch en CI).
///
/// Reglas:
/// - offline -> LocalRoute
/// - metered + batería <= 15% -> LocalRoute (data saver)
/// - wifi con RSSI < -80 -> LocalRoute (señal débil)
/// - online -> HybridRoute (edge primero, cloud si conf < 0.70)
Future<PvuRoute> route({
  required ConnectivityStatus net,
  required double batteryPct,
  RssiSample? wifi,
}) async {
  if (net == ConnectivityStatus.offline) {
    return const LocalRoute(reason: 'offline');
  }
  if (net == ConnectivityStatus.metered && batteryPct <= 0.15) {
    return const LocalRoute(reason: 'data_saver');
  }
  if (wifi != null && wifi.rssi < -80) {
    return const LocalRoute(reason: 'weak_signal');
  }
  return const HybridRoute();
}
