/// Gráficas mínimas para el panel admin (issue 15).
///
/// CustomPainter propio en vez de `fl_chart`: cero dependencias, sin riesgo
/// supply-chain y funciona offline. Solo dibuja; los datos vienen de
/// `AdminRepository` (testeado aparte). Accesibles vía `Semantics(label:)`.
library;

import 'package:flutter/material.dart';

/// Normaliza una serie a [0,1]; serie vacía o plana → línea media.
List<double> normalize(List<double> values) {
  if (values.isEmpty) return const [];
  final max = values.reduce((a, b) => a > b ? a : b);
  final min = values.reduce((a, b) => a < b ? a : b);
  if ((max - min).abs() < 1e-9) return List.filled(values.length, 0.5);
  return values.map((v) => (v - min) / (max - min)).toList();
}

class _LinePainter extends CustomPainter {
  _LinePainter(this.values, this.color);
  final List<double> values;
  final Color color;

  @override
  void paint(Canvas canvas, Size size) {
    if (values.length < 2) return;
    final paint = Paint()
      ..color = color
      ..strokeWidth = 2.5
      ..style = PaintingStyle.stroke
      ..strokeCap = StrokeCap.round;
    final path = Path();
    for (var i = 0; i < values.length; i++) {
      final x = size.width * i / (values.length - 1);
      final y = size.height * (1.0 - values[i].clamp(0.0, 1.0));
      if (i == 0) {
        path.moveTo(x, y);
      } else {
        path.lineTo(x, y);
      }
    }
    canvas.drawPath(path, paint);
  }

  @override
  bool shouldRepaint(covariant _LinePainter old) =>
      old.values != values || old.color != color;
}

class _BarPainter extends CustomPainter {
  _BarPainter(this.values, this.color);
  final List<double> values;
  final Color color;

  @override
  void paint(Canvas canvas, Size size) {
    if (values.isEmpty) return;
    final paint = Paint()..color = color;
    final slot = size.width / values.length;
    final bw = (slot * 0.6).clamp(2.0, 28.0);
    for (var i = 0; i < values.length; i++) {
      final h = size.height * values[i].clamp(0.0, 1.0);
      canvas.drawRRect(
        RRect.fromRectAndRadius(
          Rect.fromLTWH(
              slot * i + (slot - bw) / 2, size.height - h, bw, h),
          const Radius.circular(4),
        ),
        paint,
      );
    }
  }

  @override
  bool shouldRepaint(covariant _BarPainter old) =>
      old.values != values || old.color != color;
}

class _DonutPainter extends CustomPainter {
  _DonutPainter(this.fractions, this.colors);
  final List<double> fractions;
  final List<Color> colors;

  @override
  void paint(Canvas canvas, Size size) {
    final total =
        fractions.fold<double>(0, (a, b) => a + b).clamp(1e-9, double.infinity);
    final paint = Paint()
      ..style = PaintingStyle.stroke
      ..strokeWidth = size.width * 0.22;
    final rect = Rect.fromLTWH(size.width * 0.11, size.height * 0.11,
        size.width * 0.78, size.height * 0.78);
    var start = -3.141592653589793 / 2;
    for (var i = 0; i < fractions.length; i++) {
      final sweep =
          2 * 3.141592653589793 * (fractions[i] / total);
      paint.color = colors[i % colors.length];
      canvas.drawArc(rect, start, sweep, false, paint);
      start += sweep;
    }
  }

  @override
  bool shouldRepaint(covariant _DonutPainter old) =>
      old.fractions != fractions || old.colors != colors;
}

/// Serie temporal (KPIs, registros, health).
class MiniLineChart extends StatelessWidget {
  const MiniLineChart(
      {super.key, required this.values, required this.semanticLabel});

  final List<double> values;
  final String semanticLabel;

  @override
  Widget build(BuildContext context) {
    return Semantics(
      label: semanticLabel,
      child: SizedBox(
        height: 96,
        width: double.infinity,
        child: CustomPaint(
          painter: _LinePainter(
              normalize(values), Theme.of(context).colorScheme.primary),
        ),
      ),
    );
  }
}

/// Barras (p. ej. registros por día).
class MiniBarChart extends StatelessWidget {
  const MiniBarChart(
      {super.key, required this.values, required this.semanticLabel});

  final List<int> values;
  final String semanticLabel;

  @override
  Widget build(BuildContext context) {
    final max =
        values.isEmpty ? 1 : values.reduce((a, b) => a > b ? a : b).clamp(1, 1 << 31);
    return Semantics(
      label: semanticLabel,
      child: SizedBox(
        height: 96,
        width: double.infinity,
        child: CustomPaint(
          painter: _BarPainter(
              values.map((v) => v / max.toDouble()).toList(),
              Theme.of(context).colorScheme.secondary),
        ),
      ),
    );
  }
}

/// Dona (p. ej. distribución usuarios activos/inactivos).
class MiniDonutChart extends StatelessWidget {
  const MiniDonutChart(
      {super.key, required this.fractions, required this.semanticLabel});

  final List<double> fractions;
  final String semanticLabel;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Semantics(
      label: semanticLabel,
      child: SizedBox(
        height: 120,
        width: 120,
        child: CustomPaint(
          painter: _DonutPainter(
              fractions, [scheme.primary, scheme.tertiary, scheme.error]),
        ),
      ),
    );
  }
}
