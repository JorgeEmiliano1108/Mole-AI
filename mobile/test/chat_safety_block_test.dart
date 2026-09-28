/// Tests de bloqueo de seguridad en Chat RAG (Hito 5).
library;

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mole_ai/core/errors.dart';
import 'package:mole_ai/core/safety_block_banner.dart';
import 'package:mole_ai/features/chat/chat.dart';

import 'species_test.dart' show FakeAdapter, clientWith, jsonBody;

void main() {
  group('ChatAnswer safety block', () {
    test('factory safetyBlock marca respuesta bloqueada', () {
      final answer = ChatAnswer.safetyBlock(
        code: 'SAFETY_NOM059_PROTECTED',
        reason: 'Especie protegida.',
      );
      expect(answer.isSafetyBlocked, isTrue);
      expect(answer.safetyCode, 'SAFETY_NOM059_PROTECTED');
      expect(answer.safetyReason, 'Especie protegida.');
      expect(answer.response, '');
    });

    test('fromJson normal no está bloqueado', () {
      final answer = ChatAnswer.fromJson({
        'response': 'Riega por la mañana.',
        'sources': [],
        'disclaimer': 'Informativo',
      });
      expect(answer.isSafetyBlocked, isFalse);
      expect(answer.response, 'Riega por la mañana.');
    });
  });

  group('ChatRepository.send safety block', () {
    test('mapea 403 del backend a ChatAnswer bloqueada', () async {
      final api = clientWith(FakeAdapter((o) => jsonBody({
            'error': 'Especie protegida por NOM-059-SEMARNAT.',
            'code': 'SAFETY_NOM059_PROTECTED',
            'source': 'chat',
          }, 403)));
      final answer = await ChatRepository(api).send('¿cómo cuido peyote?');
      expect(answer.isSafetyBlocked, isTrue);
      expect(answer.safetyCode, 'SAFETY_NOM059_PROTECTED');
      expect(answer.safetyReason, contains('NOM-059'));
    });

    test('re-lanza excepciones que no son 403', () async {
      final api = clientWith(FakeAdapter((o) => jsonBody({
            'error': 'MS2 timeout',
          }, 503)));
      expect(
        () => ChatRepository(api).send('hola'),
        throwsA(isA<ApiException>()),
      );
    });
  });

  group('SafetyBlockBanner render in chat card', () {
    testWidgets('muestra banner cuando answer está bloqueada', (tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: SafetyBlockBanner(
              reason: 'Dosis excedida.',
              code: 'SAFETY_DOSE_EXCEEDED',
            ),
          ),
        ),
      );
      expect(find.byKey(const Key('safety_block_banner')), findsOneWidget);
      expect(find.text('Dosis excedida.'), findsOneWidget);
      expect(find.text('Código: SAFETY_DOSE_EXCEEDED'), findsOneWidget);
    });
  });
}
