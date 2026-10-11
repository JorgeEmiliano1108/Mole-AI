/// Validación de calidad de captura (FE-07, Wave F3).
///
/// Puro y testeable: luminancia media (subexposición) + varianza del
/// Laplaciano (desenfoque) sobre escala de grises. Umbrales conservadores
/// iniciales (ver `f3_crop_capture_test.dart` + gold-set): rechazar solo lo
/// evidente, jamás adivinar. El veredicto trae guía accionable, no códigos.
/// Bytes ilegibles → rechazo (no throw): la UI muestra reintento.
library;

import 'dart:typed_data';

import 'package:image/image.dart' as img;

class CaptureVerdict {
  const CaptureVerdict({required this.ok, this.reason});

  final bool ok;

  /// Guía accionable para la UI (null si [ok]).
  final String? reason;
}

/// Valida una foto antes de inferir o encolar.
///
/// - [minLuminance]: media 0..255 bajo la cual se considera a oscuras.
/// - [minSharpness]: varianza del Laplaciano bajo la cual se considera
///   borrosa/sin textura.
CaptureVerdict checkCapture(
  Uint8List jpeg, {
  double minLuminance = 25,
  double minSharpness = 15,
}) {
  // El decoder puede lanzar (RangeError) ante basura en vez de null.
  late final img.Image dec;
  try {
    final d = img.decodeImage(jpeg);
    if (d == null) throw ArgumentError('ilegible');
    dec = d;
  } catch (_) {
    return const CaptureVerdict(
        ok: false, reason: 'No se pudo leer la foto. Toma otra.');
  }
  final gray = img.grayscale(dec);
  final w = gray.width;
  final h = gray.height;
  if (w < 3 || h < 3) {
    return const CaptureVerdict(
        ok: false, reason: 'Foto demasiado pequeña. Acércate y reintenta.');
  }

  var sum = 0.0;
  for (var y = 0; y < h; y++) {
    for (var x = 0; x < w; x++) {
      sum += gray.getPixel(x, y).r.toDouble();
    }
  }
  final mean = sum / (w * h);
  if (mean < minLuminance) {
    return const CaptureVerdict(
        ok: false,
        reason: 'Muy poca luz. Busca una zona iluminada y reintenta.');
  }

  // Varianza del Laplaciano 3×3 (núcleo en cruz) en píxeles interiores.
  var sumL = 0.0;
  var sumL2 = 0.0;
  var n = 0;
  double lum(int x, int y) => gray.getPixel(x, y).r.toDouble();
  for (var y = 1; y < h - 1; y++) {
    for (var x = 1; x < w - 1; x++) {
      final l = lum(x, y - 1) +
          lum(x - 1, y) -
          4 * lum(x, y) +
          lum(x + 1, y) +
          lum(x, y + 1);
      sumL += l;
      sumL2 += l * l;
      n++;
    }
  }
  final variance = (sumL2 - sumL * sumL / n) / n;
  if (variance < minSharpness) {
    return const CaptureVerdict(
        ok: false,
        reason:
            'Imagen no nítida. Limpia la lente, mantén el pulso y reintenta.');
  }
  return const CaptureVerdict(ok: true);
}
