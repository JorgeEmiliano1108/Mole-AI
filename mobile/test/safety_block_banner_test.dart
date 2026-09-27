import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mole_ai/core/safety_block_banner.dart';

void main() {
  testWidgets('SafetyBlockBanner muestra razón y código', (tester) async {
    await tester.pumpWidget(
      const MaterialApp(
        home: Scaffold(
          body: SafetyBlockBanner(
            reason: 'Especie protegida por NOM-059-SEMARNAT.',
            code: 'SAFETY_NOM059_PROTECTED',
          ),
        ),
      ),
    );

    expect(find.byKey(const Key('safety_block_banner')), findsOneWidget);
    expect(find.text('Contenido bloqueado por seguridad'), findsOneWidget);
    expect(find.text('Especie protegida por NOM-059-SEMARNAT.'), findsOneWidget);
    expect(find.text('Código: SAFETY_NOM059_PROTECTED'), findsOneWidget);
  });

  testWidgets('SafetyBlockBanner oculta código si no se provee', (tester) async {
    await tester.pumpWidget(
      const MaterialApp(
        home: Scaffold(
          body: SafetyBlockBanner(
            reason: 'Dosis excedida.',
          ),
        ),
      ),
    );

    expect(find.byKey(const Key('safety_block_banner')), findsOneWidget);
    expect(find.text('Dosis excedida.'), findsOneWidget);
    expect(find.textContaining('Código:'), findsNothing);
  });
}
