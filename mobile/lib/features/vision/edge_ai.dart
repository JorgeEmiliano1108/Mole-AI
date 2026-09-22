/// Edge AI en dispositivo (MRF02/RNF01, F2-hito1).
///
/// Modelo stand-in `mobilenetv2_integration.tflite` (ver
/// `assets/models/README.md`): input (1,224,224,3) float32 [-1,1] →
/// output (1,8) softmax. El modelo real lo reemplaza sin cambiar esta API.
/// Veredicto: `local` si confianza ≥ threshold, si no `uncertain`
/// (el llamador usa el flujo servidor: cola + `POST diagnostics/`).
library;

import 'dart:typed_data';

import 'package:image/image.dart' as img;
import 'package:tflite_flutter/tflite_flutter.dart';

/// Intérprete inyectable (tests usan el fake; prod usa TFLite real).
abstract class EdgeInterpreter {
  Future<void> load();
  Future<List<double>> run(Float32List input);
  void close();
}

class TfliteEdgeInterpreter implements EdgeInterpreter {
  TfliteEdgeInterpreter({this.assetPath = _kAsset});

  static const _kAsset = 'assets/models/plant_mobilenetv2_38.tflite';
  static const classes = 38;

  final String assetPath;
  Interpreter? _it;

  @override
  Future<void> load() async {
    _it ??= await Interpreter.fromAsset(assetPath);
  }

  @override
  Future<List<double>> run(Float32List input) async {
    final it = _it;
    if (it == null) throw StateError('EdgeInterpreter sin load()');
    final output =
        List.filled(classes, 0.0).reshape([1, classes]);
    it.run(input.reshape([1, 224, 224, 3]), output);
    return List<double>.from(output[0]);
  }

  @override
  void close() => _it?.close();
}

class FakeEdgeInterpreter implements EdgeInterpreter {
  FakeEdgeInterpreter({List<double>? scores})
      : scores = scores ??
            ([0.9, ...List.filled(37, 0.1 / 37)]);
  final List<double> scores;
  bool loaded = false;

  @override
  Future<void> load() async => loaded = true;

  @override
  Future<List<double>> run(Float32List input) async =>
      List<double>.from(scores);

  @override
  void close() {}
}

/// Preprocesa JPEG → Float32List (1,224,224,3) normalizado [-1,1].
/// Puro Dart: testeable en host sin TFLite.
Float32List preprocessJpeg(List<int> jpegBytes) {
  final decoded = img.decodeImage(Uint8List.fromList(jpegBytes));
  if (decoded == null) throw ArgumentError('JPEG ilegible');
  final resized =
      img.copyResize(decoded, width: 224, height: 224);
  final out = Float32List(1 * 224 * 224 * 3);
  var i = 0;
  for (var y = 0; y < 224; y++) {
    for (var x = 0; x < 224; x++) {
      final p = resized.getPixel(x, y);
      out[i++] = p.r / 127.5 - 1.0;
      out[i++] = p.g / 127.5 - 1.0;
      out[i++] = p.b / 127.5 - 1.0;
    }
  }
  return out;
}

class EdgeVerdict {
  EdgeVerdict(
      {required this.local,
      required this.topClass,
      required this.confidence,
      required this.latencyMs});
  final bool local;
  final int topClass;
  final double confidence;
  final double latencyMs;
}

class EdgeAiService {
  EdgeAiService({EdgeInterpreter? interpreter, this.confidenceThreshold = 0.70})
      : _interpreter = interpreter ?? TfliteEdgeInterpreter();

  /// Umbral calibrado empíricamente con el modelo real (revisión 2026-09-19).
  final double confidenceThreshold;
  final EdgeInterpreter _interpreter;
  bool _ready = false;

  Future<EdgeVerdict> diagnose(List<int> jpegBytes) async {
    if (!_ready) {
      await _interpreter.load();
      _ready = true;
    }
    final input = preprocessJpeg(jpegBytes);
    final sw = Stopwatch()..start();
    final scores = await _interpreter.run(input);
    sw.stop();
    var top = 0;
    for (var i = 1; i < scores.length; i++) {
      if (scores[i] > scores[top]) top = i;
    }
    final conf = scores[top];
    return EdgeVerdict(
      local: conf >= confidenceThreshold,
      topClass: top,
      confidence: conf,
      latencyMs: sw.elapsedMicroseconds / 1000.0,
    );
  }

  void close() => _interpreter.close();
}
