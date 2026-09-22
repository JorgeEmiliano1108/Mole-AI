/// Tests del decoder FEE2 (spec §2/§3).
///
/// Vectores cruzados byte-por-byte con
/// `microservices/esp32_node/tests/test_fee2_frame.c` (golden 19B).
library;

import 'dart:typed_data';

import 'package:flutter_test/flutter_test.dart';
import 'package:mole_ai/features/ble/ble_telemetry.dart';

/// Golden C: ts=1699123456 ri=5 valid=0x0F t=28.4 h=65.2 l=410 u=5.5
/// sondas ch4/adc2847 + ch5/adc3012.
const _golden = [
  0x00, 0x91, 0x46, 0x65, 0x05, 0x0F, 0x18, 0x0B, 0x78, 0x19,
  0x9A, 0x01, 0x26, 0x02, 0x02, 0x4B, 0x1F, 0x5B, 0xC4,
];

void main() {
  group('BleTelemetry.decode (spec §2)', () {
    test('golden 19B: punto fijo /100', () {
      final t =
          BleTelemetry.decode(Uint8List.fromList(_golden));
      expect(t.timestamp.millisecondsSinceEpoch,
          1699123456 * 1000);
      expect(t.reportIntervalMin, 5);
      expect(t.valid, 0x0F);
      expect(t.degraded, 0);
      expect(t.temperatureC, closeTo(28.4, 0.005));
      expect(t.humidityPct, closeTo(65.2, 0.005));
      expect(t.lightLux, 410);
      expect(t.uvIndex, closeTo(5.5, 0.005));
      expect(t.soil, hasLength(2));
      expect(t.soil[0].gpio, 32);
      expect(t.soil[0].adcRaw, 2847);
      expect(t.soil[1].gpio, 33);
      expect(t.soil[1].adcRaw, 3012);
      expect(t.soil[0].humidityPct,
          closeTo((4095 - 2847) / 2595 * 100, 0.1));
    });

    test('trama mínima cabe en MTU-23', () {
      expect(_golden.length, lessThanOrEqualTo(20));
    });

    test('truncadas lanzan FormatException', () {
      expect(() => BleTelemetry.decode(Uint8List(0)),
          throwsFormatException);
      expect(
          () => BleTelemetry.decode(
              Uint8List.fromList(_golden.sublist(0, 10))),
          throwsFormatException);
      expect(
          () => BleTelemetry.decode(
              Uint8List.fromList(_golden.sublist(0, 17))),
          throwsFormatException);
    });

    test('temperatura negativa i16', () {
      // ts=1700000000 ri=5 valid=0x01 t=-5.25 (0xFDF3 LE), 0 sondas.
      final raw = [
        0x00, 0xF1, 0x53, 0x65, 0x05, 0x01, 0xF3, 0xFD, 0x00,
      ];
      final t = BleTelemetry.decode(Uint8List.fromList(raw));
      expect(t.temperatureC, closeTo(-5.25, 0.005));
      expect(t.humidityPct, isNull);
      expect(t.soil, isEmpty);
    });
  });

  group('BleFrameAssembler (spec §3)', () {
    test('fragmento único pasa directo', () {
      final a = BleFrameAssembler();
      final frame = Uint8List.fromList(_golden);
      final full = Uint8List.fromList([0, 1, ...frame]);
      expect(a.addFragment(full), orderedEquals(frame));
    });

    test('dos fragmentos se reensamblan en orden', () {
      final a = BleFrameAssembler();
      final frame = Uint8List.fromList(_golden);
      final p0 = Uint8List.fromList([0, 2, ...frame.sublist(0, 10)]);
      final p1 = Uint8List.fromList([1, 2, ...frame.sublist(10)]);
      expect(a.addFragment(p1), isNull);
      expect(a.addFragment(p0), orderedEquals(frame));
    });

    test('seq/total inválido lanza', () {
      final a = BleFrameAssembler();
      expect(() => a.addFragment(Uint8List.fromList([0])),
          throwsFormatException);
      expect(() => a.addFragment(Uint8List.fromList([2, 2, 0])),
          throwsFormatException);
    });
  });
}
