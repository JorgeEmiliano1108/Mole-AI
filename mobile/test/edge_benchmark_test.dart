/// Tests Track C: instrumentación Edge + batería (host, sin TFLite ni canal).
///
/// El intérprete real no corre en host: se usa `FakeEdgeInterpreter` con la
/// misma firma. La batería usa `FakeBatteryReader` scripteado.
library;

import 'package:flutter_test/flutter_test.dart';
import 'package:image/image.dart' as img;
import 'package:mole_ai/features/vision/edge_ai.dart';
import 'package:mole_ai/features/vision/edge_benchmark.dart';

List<int> _redJpeg() => img.encodeJpg(
    img.Image(width: 320, height: 240)..clear(img.ColorRgb8(200, 30, 30)));

void main() {
  group('InstrumentedEdgeInterpreter', () {
    test('delega y registra un timing por run', () async {
      final inner = FakeEdgeInterpreter();
      final inst = InstrumentedEdgeInterpreter(inner);
      await inst.load();
      expect(inner.loaded, isTrue);
      final scores = await inst.run(preprocessJpeg(_redJpeg()));
      expect(scores, isNotEmpty);
      expect(inst.runTimingsMs, hasLength(1));
      expect(inst.runTimingsMs.first, greaterThanOrEqualTo(0.0));
      inst.close();
    });
  });

  group('runEdgeBenchmark', () {
    test('reporta P50/P95 y pasa el SLO con fake rápido', () async {
      final report = await runEdgeBenchmark(
        interpreter: FakeEdgeInterpreter(),
        battery: FakeBatteryReader(startPct: 80.0, drainPerRead: 0.05),
        jpegBytes: _redJpeg(),
        warmupIterations: 1,
        iterations: 5,
      );
      expect(report.iterations, 5);
      expect(report.runP50Ms, greaterThanOrEqualTo(0.0));
      expect(report.runP95Ms, greaterThanOrEqualTo(report.runP50Ms));
      expect(report.totalP95Ms, greaterThanOrEqualTo(report.totalP50Ms));
      expect(report.passesLatencySlo, isTrue);
      expect(report.batteryStartPct, 80.0);
      // 1 lectura antes + 1 después, con drain 0.05 cada una.
      expect(report.batteryEndPct, closeTo(79.95, 1e-9));
      expect(report.batteryDrainPctPerHour, greaterThan(0.0));
      final j = report.toJson();
      expect(j['passes_latency_slo_850ms'], isTrue);
      expect(j['iterations'], 5);
    });

    test('timings desglosados suman el total', () async {
      final report = await runEdgeBenchmark(
        interpreter: FakeEdgeInterpreter(),
        battery: FakeBatteryReader(),
        jpegBytes: _redJpeg(),
        warmupIterations: 0,
        iterations: 3,
      );
      expect(report.totalP50Ms, greaterThanOrEqualTo(report.runP50Ms));
    });
  });
}
