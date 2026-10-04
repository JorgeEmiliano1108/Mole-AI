/// Harness Edge en DISPOSITIVO (Track C, manual).
///
/// Corre `runEdgeBenchmark` con el TFLite real + `BatteryManager` real y
/// escribe el reporte JSON en el dir temporal (la ruta se imprime en logs).
/// Requiere dispositivo físico (no emulador sin TFLite delegate).
///
/// Correr:
///   flutter test integration_test/edge_benchmark_test.dart -d <device-id>
/// Ver `.scratch/harness-empirico/PROTOCOLO-C3.md` para el protocolo completo.
library;

import 'dart:convert';
import 'dart:io';

import 'package:flutter_test/flutter_test.dart';
import 'package:image/image.dart' as img;
import 'package:integration_test/integration_test.dart';
import 'package:mole_ai/features/vision/edge_ai.dart';
import 'package:mole_ai/features/vision/edge_benchmark.dart';
import 'package:path_provider/path_provider.dart';

List<int> _benchJpeg() => img.encodeJpg(
    img.Image(width: 640, height: 480)..clear(img.ColorRgb8(60, 140, 60)));

void main() {
  IntegrationTestWidgetsFlutterBinding.ensureInitialized();

  testWidgets('edge benchmark en dispositivo', (_) async {
    final report = await runEdgeBenchmark(
      interpreter: TfliteEdgeInterpreter(),
      battery: MethodChannelBatteryReader(),
      jpegBytes: _benchJpeg(),
      warmupIterations: 3,
      // Ventana de batería: ~200 inferencias para un delta medible.
      // Ajustar según PROTOCOLO-C3 (gama baja: 100 para no agotar).
      iterations: int.fromEnvironment('BENCH_ITERS', defaultValue: 200),
    );

    final dir = await getTemporaryDirectory();
    final file = File(
        '${dir.path}/edge_benchmark_${DateTime.now().toUtc().toIso8601String().replaceAll(':', '-')}.json');
    await file.writeAsString(jsonEncode(report.toJson()));
    // ignore: avoid_print
    print('EDGE_BENCHMARK_JSON: ${jsonEncode(report.toJson())}');
    // ignore: avoid_print
    print('EDGE_BENCHMARK_FILE: ${file.path}');

    expect(report.iterations, greaterThan(0));
  }, timeout: const Timeout(Duration(minutes: 30)));
}
