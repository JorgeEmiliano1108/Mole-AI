/// Recorte ROI interactivo (FE-03, Wave F3).
///
/// Matemática pura (testeable sin widgets): rectángulo normalizado sobre la
/// foto original + recorte con `package:image` (ya es dependencia, sin
/// cambios en `pubspec`). La UI vive en `diagnosis_screen.dart` (bottom-sheet);
/// aquí solo el núcleo. Bytes ilegibles → [ArgumentError], igual que
/// `edge_ai.dart` (`preprocessJpeg`).
library;

import 'dart:typed_data';

import 'package:flutter/material.dart';
import 'package:image/image.dart' as img;

/// Rectángulo normalizado 0..1 sobre la imagen original.
class RoiRect {
  const RoiRect({
    required this.left,
    required this.top,
    required this.width,
    required this.height,
  });

  /// Frame completo (default: sin recorte, la foto pasa intacta).
  static const full = RoiRect(left: 0, top: 0, width: 1, height: 1);

  final double left;
  final double top;
  final double width;
  final double height;
}

/// Recorta [roi] de un JPEG y devuelve JPEG. Sujeta a bordes (clamp),
/// expande al mínimo [minPx] y nunca revienta: solo [ArgumentError] ante
/// bytes ilegibles.
Uint8List cropRoi(Uint8List jpeg, RoiRect roi, {int minPx = 64}) {
  // El decoder puede lanzar RangeError ante basura (no solo null):
  // se normaliza a ArgumentError, igual que `edge_ai.dart`.
  late final img.Image dec;
  try {
    final d = img.decodeImage(jpeg);
    if (d == null) throw ArgumentError('JPEG ilegible');
    dec = d;
  } catch (_) {
    throw ArgumentError('JPEG ilegible');
  }
  final w = dec.width;
  final h = dec.height;

  var x = (roi.left * w).round();
  var y = (roi.top * h).round();
  var cw = (roi.width * w).round();
  var ch = (roi.height * h).round();

  x = x.clamp(0, w - 1);
  y = y.clamp(0, h - 1);
  cw = cw.clamp(1, w - x);
  ch = ch.clamp(1, h - y);

  // Expande al mínimo centrado en el rect pedido (sin salirse).
  if (cw < minPx || ch < minPx) {
    final cx = x + cw ~/ 2;
    final cy = y + ch ~/ 2;
    cw = cw < minPx ? minPx.clamp(1, w) : cw;
    ch = ch < minPx ? minPx.clamp(1, h) : ch;
    x = (cx - cw ~/ 2).clamp(0, w - cw);
    y = (cy - ch ~/ 2).clamp(0, h - ch);
  }

  return img.encodeJpg(img.copyCrop(dec, x: x, y: y, width: cw, height: ch));
}

/// Bottom-sheet de recorte ROI (FE-03).
///
/// Rectángulo simple: se arrastra para mover, slider para tamaño.
/// Confirmar → [RoiRect]; Cancelar → null (= frame completo, cero bloqueo).
/// Testeable directo ([RoiCropSheet]) sin Navigator.
Future<RoiRect?> showRoiCropSheet(BuildContext context, Uint8List jpeg) {
  return showModalBottomSheet<RoiRect>(
    context: context,
    isScrollControlled: true,
    builder: (_) => RoiCropSheet(
      jpeg: jpeg,
      onConfirm: (r) => Navigator.of(context).pop(r),
      onCancel: () => Navigator.of(context).pop(),
    ),
  );
}

class RoiCropSheet extends StatefulWidget {
  const RoiCropSheet(
      {super.key,
      required this.jpeg,
      required this.onConfirm,
      required this.onCancel});

  final Uint8List jpeg;
  final ValueChanged<RoiRect> onConfirm;
  final VoidCallback onCancel;

  @override
  State<RoiCropSheet> createState() => _RoiCropSheetState();
}

class _RoiCropSheetState extends State<RoiCropSheet> {
  // Centro + lado (fracción del lado corto) del rect en coords normalizadas.
  double _cx = 0.5;
  double _cy = 0.5;
  double _side = 0.8;

  RoiRect get _rect => RoiRect(
        left: (_cx - _side / 2).clamp(0.0, 1.0),
        top: (_cy - _side / 2).clamp(0.0, 1.0),
        width: _side,
        height: _side,
      );

  @override
  Widget build(BuildContext context) {
    return SafeArea(
      // Scrollable: en pantallas chicas el Column desbordaba (misma clase
      // de bug que DiagnosisScreen a 600px; aquí sí se corrige).
      child: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            const Text('Recorta la hoja',
                style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
            const SizedBox(height: 8),
            AspectRatio(
              aspectRatio: 4 / 3,
              child: LayoutBuilder(builder: (context, box) {
                return GestureDetector(
                  onPanUpdate: (d) {
                    setState(() {
                      _cx = (_cx + d.delta.dx / box.maxWidth)
                          .clamp(_side / 2, 1 - _side / 2);
                      _cy = (_cy + d.delta.dy / box.maxHeight)
                          .clamp(_side / 2, 1 - _side / 2);
                    });
                  },
                  child: Stack(
                    fit: StackFit.expand,
                    children: [
                      Image.memory(widget.jpeg, fit: BoxFit.cover),
                      CustomPaint(painter: _RoiOverlay(_rect)),
                    ],
                  ),
                );
              }),
            ),
            Row(
              children: [
                const Text('Tamaño'),
                Expanded(
                  child: Slider(
                    value: _side,
                    min: 0.3,
                    max: 1.0,
                    divisions: 7,
                    label: '${(_side * 100).round()}%',
                    onChanged: (v) => setState(() {
                      _side = v;
                      _cx = _cx.clamp(v / 2, 1 - v / 2);
                      _cy = _cy.clamp(v / 2, 1 - v / 2);
                    }),
                  ),
                ),
              ],
            ),
            Row(
              children: [
                Expanded(
                  child: OutlinedButton(
                      onPressed: widget.onCancel,
                      child: const Text('Cancelar')),
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: FilledButton(
                      onPressed: () => widget.onConfirm(_rect),
                      child: const Text('Confirmar recorte')),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

/// Máscara oscura con ventana del ROI (misma convención normalizada
/// full-box que el gesto: sin sorpresas entre dedo y dibujo).
class _RoiOverlay extends CustomPainter {
  _RoiOverlay(this.roi);

  final RoiRect roi;

  @override
  void paint(Canvas canvas, Size size) {
    final rect = Rect.fromLTWH(
      roi.left * size.width,
      roi.top * size.height,
      roi.width * size.width,
      roi.height * size.height,
    );
    canvas.drawPath(
      Path()
        ..addRect(Rect.fromLTWH(0, 0, size.width, size.height))
        ..addRect(rect)
        ..fillType = PathFillType.evenOdd,
      Paint()..color = const Color(0x99000000),
    );
    canvas.drawRect(
        rect, Paint()..color = const Color(0xFFFFFFFF)..style = PaintingStyle.stroke..strokeWidth = 2);
  }

  @override
  bool shouldRepaint(covariant _RoiOverlay old) => old.roi != roi;
}
