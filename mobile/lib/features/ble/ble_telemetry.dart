/// Telemetría BLE en vivo (FEE2, spec `gatt-fee2-spec.md` §2/§3).
///
/// Decoder puro del formato punto-fijo LE (mirror de `fee2_frame.c`):
/// `ts:u32 | ri:u8 | valid:u8 | t?:i16 | h?:u16 | l?:u16 | u?:u16`
/// `| soil_count:u8 | N×{ch(3b)+adc(12b)}`. La app divide ×100.
/// Sin tokens ni PII: solo magnitudes de sensor (LFPDPPP).
library;

import 'dart:typed_data';

/// GPIO por canal ADC1 (inverso de `MOLE_GPIO_TO_ADC1_CHANNEL`).
const bleChannelToGpio = {
  0: 36,
  1: 37,
  2: 38,
  3: 39,
  4: 32,
  5: 33,
  6: 34,
  7: 35,
};

/// Calibración capacitiva (mirror `mole_config.h`).
const bleSoilAirAdc = 4095;
const bleSoilWaterAdc = 1500;

class BleSoilProbe {
  const BleSoilProbe({required this.gpio, required this.adcRaw});

  /// GPIO 32–39.
  final int gpio;

  /// ADC crudo 12-bit 0–4095.
  final int adcRaw;

  /// Humedad % estimada (clamp 0–100). Solo presentación.
  double get humidityPct {
    final v = (bleSoilAirAdc - adcRaw) /
        (bleSoilAirAdc - bleSoilWaterAdc) *
        100.0;
    return v.clamp(0.0, 100.0);
  }
}

class BleTelemetry {
  const BleTelemetry({
    required this.timestamp,
    required this.reportIntervalMin,
    required this.valid,
    this.temperatureC,
    this.humidityPct,
    this.lightLux,
    this.uvIndex,
    this.soil = const [],
  });

  final DateTime timestamp;
  final int reportIntervalMin;

  /// Bitmask: bit0=t bit1=h bit2=l bit3=u.
  final int valid;
  final double? temperatureC;
  final double? humidityPct;
  final int? lightLux;
  final double? uvIndex;
  final List<BleSoilProbe> soil;

  /// `dg = ~valid & 0x0F` (mirror `edge_frame.h`).
  int get degraded => (~valid) & 0x0F;

  /// Decodifica una trama completa (post-reensamblado). Lanza
  /// [FormatException] si está truncada o vacía.
  factory BleTelemetry.decode(Uint8List bytes) {
    final data = ByteData.sublistView(bytes);
    if (bytes.length < 7) {
      throw FormatException(
          'Trama FEE2 truncada: ${bytes.length}B < 7B', bytes);
    }
    var o = 0;
    final ts = data.getUint32(o, Endian.little);
    o += 4;
    final ri = data.getUint8(o++);
    final valid = data.getUint8(o++) & 0x0F;

    double? t, h, u;
    int? l;
    int need = 7;
    if (valid & 0x01 != 0) need += 2;
    if (valid & 0x02 != 0) need += 2;
    if (valid & 0x04 != 0) need += 2;
    if (valid & 0x08 != 0) need += 2;
    if (bytes.length < need) {
      throw FormatException(
          'Trama FEE2 truncada: ${bytes.length}B < $need B', bytes);
    }
    if (valid & 0x01 != 0) {
      t = data.getInt16(o, Endian.little) / 100.0;
      o += 2;
    }
    if (valid & 0x02 != 0) {
      h = data.getUint16(o, Endian.little) / 100.0;
      o += 2;
    }
    if (valid & 0x04 != 0) {
      l = data.getUint16(o, Endian.little);
      o += 2;
    }
    if (valid & 0x08 != 0) {
      u = data.getUint16(o, Endian.little) / 100.0;
      o += 2;
    }
    final count = data.getUint8(o++);
    if (bytes.length < o + 2 * count) {
      throw FormatException(
          'Sondas FEE2 truncadas: faltan bytes', bytes);
    }
    final soil = <BleSoilProbe>[];
    for (var i = 0; i < count; i++) {
      final b0 = data.getUint8(o++);
      final b1 = data.getUint8(o++);
      final ch = (b0 >> 4) & 0x07;
      final adc = ((b0 & 0x0F) << 8) | b1;
      soil.add(BleSoilProbe(
          gpio: bleChannelToGpio[ch] ?? -1, adcRaw: adc));
    }
    return BleTelemetry(
      timestamp:
          DateTime.fromMillisecondsSinceEpoch(ts * 1000, isUtc: true),
      reportIntervalMin: ri,
      valid: valid,
      temperatureC: t,
      humidityPct: h,
      lightLux: l,
      uvIndex: u,
      soil: soil,
    );
  }
}

/// Reensambla fragmentos `[seq:u8][total:u8][chunk…]` (spec §3).
/// Caso único (`seq=0, total=1`) pasa directo. Retorna la trama completa
/// al llegar el último fragmento pendiente, `null` en otro caso.
/// `reset()` ante timeout (5 s, lo gestiona el llamador).
class BleFrameAssembler {
  final Map<int, Uint8List> _parts = {};
  int? _total;

  Uint8List? addFragment(Uint8List fragment) {
    if (fragment.length < 2) {
      throw FormatException('Fragmento FEE2 < 2B', fragment);
    }
    final seq = fragment[0];
    final total = fragment[1];
    if (total == 0 || seq >= total) {
      throw FormatException('seq/total FEE2 inválido', fragment);
    }
    if (_total != null && _total != total) _parts.clear();
    _total = total;
    _parts[seq] = fragment.sublist(2);
    if (_parts.length == total) {
      final out = BytesBuilder();
      for (var i = 0; i < total; i++) {
        out.add(_parts[i]!);
      }
      reset();
      return out.toBytes();
    }
    return null;
  }

  void reset() {
    _parts.clear();
    _total = null;
  }
}
