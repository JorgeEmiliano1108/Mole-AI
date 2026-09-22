/// Tests F2-hito1/hito2: preproceso + umbral de fallback (MRF02).
///
/// El intérprete real (TFLite nativo) no corre en host: se usa el fake con
/// la misma firma. La validez del `.tflite` se probó con ai-edge-litert
/// (softmax=1.0) al generarlo — ver `assets/models/README.md`.
library;

import 'dart:io';

import 'package:flutter_test/flutter_test.dart';
import 'package:image/image.dart' as img;
import 'package:mole_ai/features/vision/edge_ai.dart';

List<int> _redJpeg() => img.encodeJpg(
    img.Image(width: 320, height: 240)..clear(img.ColorRgb8(200, 30, 30)));

void main() {
  group('preprocessJpeg (puro Dart)', () {
    test('forma (150528) y rango [-1,1]', () {
      final out = preprocessJpeg(_redJpeg());
      expect(out.length, 224 * 224 * 3);
      var lo = 2.0, hi = -2.0;
      for (final v in out) {
        if (v < lo) lo = v;
        if (v > hi) hi = v;
      }
      expect(lo, greaterThanOrEqualTo(-1.0));
      expect(hi, lessThanOrEqualTo(1.0));
      // Rojo dominante → canal R positivo.
      expect(out[0], greaterThan(0.0));
    });

    test('JPEG ilegible lanza ArgumentError', () {
      expect(() => preprocessJpeg([0, 1, 2, 3]),
          throwsA(isA<ArgumentError>()));
    });
  });

  group('EdgeAiService threshold (hito 2)', () {
    test('confianza alta → veredicto local', () async {
      final svc = EdgeAiService(
          interpreter: FakeEdgeInterpreter(), confidenceThreshold: 0.6);
      final v = await svc.diagnose(_redJpeg());
      expect(v.local, isTrue);
      expect(v.topClass, 0);
      expect(v.confidence, closeTo(0.9, 0.001));
      expect(v.latencyMs, greaterThanOrEqualTo(0.0));
    });

    test('confianza baja → uncertain (va a servidor/cola)', () async {
      final svc = EdgeAiService(
          interpreter: FakeEdgeInterpreter(
              scores: const [0.2, 0.15, 0.15, 0.1, 0.1, 0.1, 0.1, 0.1]),
          confidenceThreshold: 0.6);
      final v = await svc.diagnose(_redJpeg());
      expect(v.local, isFalse);
    });

    test('modelo real uniforme da confianza ~1/38 → siempre fallback', () async {
      // El FP16 real con entrada neutra tiende a uniforme: bajo el threshold
      // 0.70 va al servidor. Determinista para el contrato de fallback.
      final svc = EdgeAiService(
          interpreter: FakeEdgeInterpreter(
              scores: List.filled(38, 1 / 38)),
          confidenceThreshold: 0.7);
      final v = await svc.diagnose(_redJpeg());
      expect(v.local, isFalse);
    });

    test('threshold por defecto es 0.70 (directriz arquitectónica)', () {
      final svc = EdgeAiService(interpreter: FakeEdgeInterpreter());
      expect(svc.confidenceThreshold, 0.70);
    });
  });

  group('Contrato de assets F4 (MRF02)', () {
    test('labels.txt tiene 38 líneas en orden canónico', () async {
      final lines = await File('assets/models/labels.txt').readAsLines();
      expect(lines, hasLength(38));
      expect(lines.first, 'Apple___Apple_scab');
      expect(lines.any((l) => l.startsWith('Tomato___')), isTrue);
    });

    test('pubspec declara modelo + labels (bundle APK)', () async {
      final pubspec = await File('pubspec.yaml').readAsString();
      expect(pubspec, contains('assets/models/plant_mobilenetv2_38.tflite'));
      expect(pubspec, contains('assets/models/labels.txt'));
      expect(pubspec, isNot(contains('mobilenetv2_integration')));
    });
  });
}
