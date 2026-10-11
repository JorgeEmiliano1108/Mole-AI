/// Wave F3 (FE-03 + FE-07): ROI crop + validación de captura.
///
/// TDD: rojo contra código inexistente (`roi_crop.dart`, `capture_check.dart`).
library;

import 'dart:typed_data';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:image/image.dart' as img;
import 'package:mole_ai/features/vision/capture_check.dart';
import 'package:mole_ai/features/vision/roi_crop.dart';

/// JPEG sintético de 200×200 con borde (alta varianza = nítido y claro).
Uint8List _sharpBright() {
  final im = img.Image(width: 200, height: 200);
  img.fill(im, color: img.ColorRgb8(200, 200, 200));
  for (var x = 40; x < 160; x++) {
    for (var y = 40; y < 160; y++) {
      im.setPixel(x, y, img.ColorRgb8(20, 120, 20));
    }
  }
  return img.encodeJpg(im);
}

/// JPEG casi negro (subexpuesto).
Uint8List _dark() {
  final im = img.Image(width: 200, height: 200);
  img.fill(im, color: img.ColorRgb8(8, 8, 8));
  return img.encodeJpg(im);
}

/// JPEG gris plano (varianza ~0 = borroso/sin textura).
Uint8List _flat() {
  final im = img.Image(width: 200, height: 200);
  img.fill(im, color: img.ColorRgb8(128, 128, 128));
  return img.encodeJpg(im);
}

void main() {
  group('cropRoi (FE-03)', () {
    test('recorte centrado 50% da dimensiones exactas', () {
      final out = cropRoi(
        _sharpBright(),
        const RoiRect(left: 0.25, top: 0.25, width: 0.5, height: 0.5),
      );
      final dec = img.decodeImage(out)!;
      expect(dec.width, 100);
      expect(dec.height, 100);
    });

    test('rect fuera de bordes se sujeta (clamp), no revienta', () {
      final out = cropRoi(
        _sharpBright(),
        const RoiRect(left: -0.5, top: -0.5, width: 3, height: 3),
      );
      final dec = img.decodeImage(out)!;
      expect(dec.width, 200);
      expect(dec.height, 200);
    });

    test('rect minúsculo se expande al mínimo 64px', () {
      final out = cropRoi(
        _sharpBright(),
        const RoiRect(left: 0.4, top: 0.4, width: 0.01, height: 0.01),
      );
      final dec = img.decodeImage(out)!;
      expect(dec.width, greaterThanOrEqualTo(64));
      expect(dec.height, greaterThanOrEqualTo(64));
    });

    test('bytes ilegibles lanzan ArgumentError (como edge_ai)', () {
      expect(
        () => cropRoi(Uint8List.fromList([0, 1, 2, 3]),
            const RoiRect(left: 0, top: 0, width: 1, height: 1)),
        throwsArgumentError,
      );
    });
  });

  group('checkCapture (FE-07)', () {
    test('foto sana pasa', () {
      final v = checkCapture(_sharpBright());
      expect(v.ok, isTrue, reason: v.reason);
    });

    test('foto oscura se rechaza con guía accionable', () {
      final v = checkCapture(_dark());
      expect(v.ok, isFalse);
      expect(v.reason, contains('luz'));
    });

    test('foto plana (borrosa/sin textura) se rechaza', () {
      final v = checkCapture(_flat());
      expect(v.ok, isFalse);
      expect(v.reason, contains('nítida'));
    });

    test('bytes ilegibles se rechazan, no revientan', () {
      final v = checkCapture(Uint8List.fromList([0, 1, 2, 3]));
      expect(v.ok, isFalse);
    });
  });

  group('RoiCropSheet (FE-03)', () {
    testWidgets('Confirmar devuelve rect válido', (t) async {
      RoiRect? got;
      var cancelled = false;
      await t.pumpWidget(MaterialApp(
        home: Scaffold(
          body: RoiCropSheet(
            jpeg: _sharpBright(),
            onConfirm: (r) => got = r,
            onCancel: () => cancelled = true,
          ),
        ),
      ));
      await t.pump();
      await t.scrollUntilVisible(find.text('Confirmar recorte'), 200);
      await t.tap(find.text('Confirmar recorte'));
      await t.pump();
      expect(cancelled, isFalse);
      expect(got, isNotNull);
      expect(got!.width, greaterThan(0));
      expect(got!.height, greaterThan(0));
    });

    testWidgets('Cancelar devuelve null (frame completo)', (t) async {
      RoiRect? got = const RoiRect(left: 0, top: 0, width: 1, height: 1);
      var cancelled = false;
      await t.pumpWidget(MaterialApp(
        home: Scaffold(
          body: RoiCropSheet(
            jpeg: _sharpBright(),
            onConfirm: (r) => got = r,
            onCancel: () {
              cancelled = true;
              got = null;
            },
          ),
        ),
      ));
      await t.pump();
      await t.scrollUntilVisible(find.text('Cancelar'), 200);
      await t.tap(find.text('Cancelar'));
      await t.pump();
      expect(cancelled, isTrue);
      expect(got, isNull);
    });
  });
}
