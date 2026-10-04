/// Harness empírico Edge (Track C): latencia + batería.
///
/// - `InstrumentedEdgeInterpreter`: envuelve cualquier `EdgeInterpreter` sin
///   cambiar semántica; registra el tiempo de `run` por invocación.
/// - `EdgeBenchmark`: separa tiempos preprocess / run / threshold, reporta
///   P50/P95 y veredicto contra el umbral RNF (<850 ms).
/// - `BatteryReader`: lee nivel de batería vía `MethodChannel` (`mole.ai/battery`
///   → `getBatteryPct`, implementado en `MainActivity.kt`); en tests se usa
///   el fake. El drenaje se extrapola a %/h con advertencia de ruido en
///   ventanas cortas (ver PROTOCOLO-C3).
library;

import 'dart:typed_data';

import 'package:flutter/services.dart';
import 'package:mole_ai/features/vision/edge_ai.dart';

/// Umbral RNF de latencia de inferencia Edge (ms).
const double kEdgeLatencySloMs = 850.0;

/// Tiempos desglosados de una inferencia (ms).
class EdgeTimings {
  EdgeTimings({
    required this.preprocessMs,
    required this.runMs,
    required this.thresholdMs,
  });

  final double preprocessMs;
  final double runMs;
  final double thresholdMs;
  double get totalMs => preprocessMs + runMs + thresholdMs;

  Map<String, double> toJson() => {
        'preprocess_ms': preprocessMs,
        'run_ms': runMs,
        'threshold_ms': thresholdMs,
        'total_ms': totalMs,
      };
}

/// Envuelve un intérprete y registra `runMs` de cada invocación.
class InstrumentedEdgeInterpreter implements EdgeInterpreter {
  InstrumentedEdgeInterpreter(this.inner);

  final EdgeInterpreter inner;
  final List<double> runTimingsMs = [];

  @override
  Future<void> load() => inner.load();

  @override
  Future<List<double>> run(Float32List input) async {
    final sw = Stopwatch()..start();
    try {
      return await inner.run(input);
    } finally {
      sw.stop();
      runTimingsMs.add(sw.elapsedMicroseconds / 1000.0);
    }
  }

  @override
  void close() => inner.close();
}

/// Fuente de nivel de batería (0–100).
abstract class BatteryReader {
  Future<double> getBatteryPct();
}

/// Lee `BatteryManager` vía platform channel (Android).
class MethodChannelBatteryReader implements BatteryReader {
  MethodChannelBatteryReader({MethodChannel? channel})
      : _channel = channel ?? const MethodChannel('mole.ai/battery');

  final MethodChannel _channel;

  @override
  Future<double> getBatteryPct() async {
    final v = await _channel.invokeMethod<double>('getBatteryPct');
    if (v == null) throw StateError('BatteryChannel sin lectura');
    return v;
  }
}

/// Batería scripteada para tests (desciende [drainPerRead] por lectura).
class FakeBatteryReader implements BatteryReader {
  FakeBatteryReader({this.startPct = 80.0, this.drainPerRead = 0.05});

  double startPct;
  final double drainPerRead;

  @override
  Future<double> getBatteryPct() async {
    final v = startPct;
    startPct = (startPct - drainPerRead).clamp(0.0, 100.0);
    return v;
  }
}

/// Reporte agregado de una corrida del harness.
class EdgeBenchmarkReport {
  EdgeBenchmarkReport({
    required this.iterations,
    required this.runP50Ms,
    required this.runP95Ms,
    required this.totalP50Ms,
    required this.totalP95Ms,
    required this.passesLatencySlo,
    required this.batteryStartPct,
    required this.batteryEndPct,
    required this.batteryDrainPctPerHour,
    required this.elapsedSeconds,
  });

  final int iterations;
  final double runP50Ms;
  final double runP95Ms;
  final double totalP50Ms;
  final double totalP95Ms;
  final bool passesLatencySlo;
  final double batteryStartPct;
  final double batteryEndPct;
  final double batteryDrainPctPerHour;
  final double elapsedSeconds;

  Map<String, Object> toJson() => {
        'iterations': iterations,
        'run_p50_ms': runP50Ms,
        'run_p95_ms': runP95Ms,
        'total_p50_ms': totalP50Ms,
        'total_p95_ms': totalP95Ms,
        'passes_latency_slo_850ms': passesLatencySlo,
        'battery_start_pct': batteryStartPct,
        'battery_end_pct': batteryEndPct,
        'battery_drain_pct_per_hour': batteryDrainPctPerHour,
        'elapsed_seconds': elapsedSeconds,
      };
}

double _percentile(List<double> sorted, double p) {
  if (sorted.isEmpty) return 0.0;
  final i = ((sorted.length - 1) * p).round().clamp(0, sorted.length - 1);
  return sorted[i];
}

/// Corre el benchmark: warmup + N iteraciones con tiempos separados.
///
/// `jpegBytes` debe ser un JPEG válido (en `integration_test` se genera
/// programáticamente). No cambia la semántica de inferencia.
Future<EdgeBenchmarkReport> runEdgeBenchmark({
  required EdgeInterpreter interpreter,
  required BatteryReader battery,
  required List<int> jpegBytes,
  int warmupIterations = 3,
  int iterations = 50,
  double confidenceThreshold = 0.70,
  double latencySloMs = kEdgeLatencySloMs,
}) async {
  await interpreter.load();
  final instrumented = InstrumentedEdgeInterpreter(interpreter);

  for (var i = 0; i < warmupIterations; i++) {
    await instrumented.run(preprocessJpeg(jpegBytes));
  }
  instrumented.runTimingsMs.clear();

  final batteryStart = await battery.getBatteryPct();
  final wall = Stopwatch()..start();
  final timings = <EdgeTimings>[];
  for (var i = 0; i < iterations; i++) {
    final swPre = Stopwatch()..start();
    final input = preprocessJpeg(jpegBytes);
    swPre.stop();

    final before = instrumented.runTimingsMs.length;
    final scores = await instrumented.run(input);
    final runMs = instrumented.runTimingsMs.length > before
        ? instrumented.runTimingsMs.last
        : 0.0;

    final swThr = Stopwatch()..start();
    var top = 0;
    for (var j = 1; j < scores.length; j++) {
      if (scores[j] > scores[top]) top = j;
    }
    final conf = scores[top];
    // El veredicto local/global lo decide el llamador (PVU); aquí solo se mide.
    _ = conf >= confidenceThreshold;
    swThr.stop();

    timings.add(EdgeTimings(
      preprocessMs: swPre.elapsedMicroseconds / 1000.0,
      runMs: runMs,
      thresholdMs: swThr.elapsedMicroseconds / 1000.0,
    ));
  }
  wall.stop();
  final batteryEnd = await battery.getBatteryPct();

  final runs = timings.map((t) => t.runMs).toList()..sort();
  final totals = timings.map((t) => t.totalMs).toList()..sort();
  final elapsedH = wall.elapsedMicroseconds / 1e6 / 3600.0;
  final drainPerHour =
      elapsedH > 0 ? (batteryStart - batteryEnd) / elapsedH : 0.0;

  return EdgeBenchmarkReport(
    iterations: iterations,
    runP50Ms: _percentile(runs, 0.50),
    runP95Ms: _percentile(runs, 0.95),
    totalP50Ms: _percentile(totals, 0.50),
    totalP95Ms: _percentile(totals, 0.95),
    passesLatencySlo: totals.every((t) => t < latencySloMs),
    batteryStartPct: batteryStart,
    batteryEndPct: batteryEnd,
    batteryDrainPctPerHour: drainPerHour,
    elapsedSeconds: wall.elapsedMicroseconds / 1e6,
  );
}
