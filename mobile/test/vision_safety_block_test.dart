import 'package:flutter_test/flutter_test.dart';
import 'package:mole_ai/features/vision/vision.dart';

void main() {
  group('VisionStatus safety_block parsing', () {
    test('detecta bloqueo de seguridad con code y reason', () {
      final status = VisionStatus.fromJson({
        'status': 'success',
        'state': 'SUCCESS',
        'result': {
          'blocked': true,
          'safety_block': {
            'code': 'SAFETY_NOM059_PROTECTED',
            'reason': 'Especie protegida por NOM-059-SEMARNAT.',
          },
        },
      });

      expect(status.isSafetyBlocked, isTrue);
      expect(status.safetyCode, 'SAFETY_NOM059_PROTECTED');
      expect(status.safetyReason, 'Especie protegida por NOM-059-SEMARNAT.');
      expect(status.isSuccess, isFalse);
      expect(status.isFailure, isTrue);
      expect(status.diagnosis, isNull);
    });

    test('diagnóstico normal no está bloqueado', () {
      final status = VisionStatus.fromJson({
        'status': 'success',
        'state': 'SUCCESS',
        'result': {
          'diagnosis': {
            'species_common': 'Tomate',
            'species_scientific': 'Solanum lycopersicum',
            'affliction_name': 'Mildiu',
            'affliction_type': 'fungal',
            'severity': 'medium',
            'confidence': 0.91,
            'ph_predicted': 6.5,
            'immediate_actions': ['Aplicar azufre orgánico'],
            'disclaimer': 'Solo informativo',
          },
        },
      });

      expect(status.isSafetyBlocked, isFalse);
      expect(status.safetyCode, isNull);
      expect(status.safetyReason, isNull);
      expect(status.isSuccess, isTrue);
      expect(status.isFailure, isFalse);
      expect(status.diagnosis, isNotNull);
      expect(status.diagnosis!.speciesCommon, 'Tomate');
    });

    test('failure clásico sin safety_block no marca bloqueado', () {
      final status = VisionStatus.fromJson({
        'status': 'failure',
        'state': 'FAILURE',
        'error': 'MS1 timeout',
      });

      expect(status.isSafetyBlocked, isFalse);
      expect(status.isFailure, isTrue);
    });
  });
}
