import 'package:flutter_test/flutter_test.dart';
import 'package:mole_ai/pvu/routing.dart';

void main() {
  group('PVU route', () {
    test('offline siempre elige LocalRoute', () async {
      final r = await route(
          net: ConnectivityStatus.offline, batteryPct: 1.0, wifi: null);
      expect(r, isA<LocalRoute>());
      expect(r.reason, 'offline');
      expect(r.endpoint, 'edge');
    });

    test('metered + batería baja elige LocalRoute por data saver', () async {
      final r = await route(
          net: ConnectivityStatus.metered, batteryPct: 0.10, wifi: null);
      expect(r, isA<LocalRoute>());
      expect(r.reason, 'data_saver');
    });

    test('señal débil (< -80 dBm) elige LocalRoute', () async {
      final r = await route(
          net: ConnectivityStatus.online,
          batteryPct: 1.0,
          wifi: const RssiSample(-85));
      expect(r, isA<LocalRoute>());
      expect(r.reason, 'weak_signal');
    });

    test('online por defecto elige HybridRoute', () async {
      final r =
          await route(net: ConnectivityStatus.online, batteryPct: 1.0, wifi: null);
      expect(r, isA<HybridRoute>());
      expect(r.endpoint, 'edge_then_cloud');
    });

    test('la decisión tarda menos de 2 s (gate CI)', () async {
      final sw = Stopwatch()..start();
      await route(net: ConnectivityStatus.online, batteryPct: 1.0, wifi: null);
      sw.stop();
      expect(sw.elapsedMilliseconds, lessThan(2000));
    });
  });
}
