/// Pantallas de acceso: login, registro y consentimiento LFPDPPP.
///
/// Accesibles: scroll + SafeArea (texto grande), validación con mensajes,
/// autofill nativo, errores anunciados (liveRegion).
library;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import 'package:mole_ai/features/auth/auth_controller.dart';

String? _required(String? v) =>
    v == null || v.trim().isEmpty ? 'Requerido' : null;

class LoginScreen extends ConsumerStatefulWidget {
  /// `registerMode`: abre directo en registro (ruta `/registro`).
  const LoginScreen({super.key, this.registerMode = false});

  final bool registerMode;

  @override
  ConsumerState<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends ConsumerState<LoginScreen> {
  final _form = GlobalKey<FormState>();
  final _user = TextEditingController();
  final _pass = TextEditingController();
  bool _showRegister = false;
  bool _consent = false;

  @override
  void initState() {
    super.initState();
    _showRegister = widget.registerMode;
  }

  @override
  void dispose() {
    _user.dispose();
    _pass.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final auth = ref.watch(authControllerProvider);
    final loading = auth.status == AuthStatus.loading;
    return Scaffold(
      appBar: AppBar(title: const Text('Mole.AI')),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(24),
          child: AutofillGroup(
            child: Form(
              key: _form,
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  const SizedBox(height: 48),
                  TextFormField(
                    controller: _user,
                    decoration: const InputDecoration(
                        labelText: 'Usuario o email'),
                    keyboardType: TextInputType.emailAddress,
                    autofillHints: const [AutofillHints.username],
                    textInputAction: TextInputAction.next,
                    enabled: !loading,
                    validator: _required,
                  ),
                  const SizedBox(height: 12),
                  TextFormField(
                    controller: _pass,
                    decoration:
                        const InputDecoration(labelText: 'Contraseña'),
                    obscureText: true,
                    enableSuggestions: false,
                    autocorrect: false,
                    autofillHints: const [AutofillHints.password],
                    textInputAction: TextInputAction.done,
                    enabled: !loading,
                    validator: _required,
                    onFieldSubmitted: (_) => _submit(),
                  ),
                  const SizedBox(height: 8),
                  if (auth.error != null)
                    Semantics(
                      liveRegion: true,
                      child: Text(auth.error!,
                          style: TextStyle(
                              color:
                                  Theme.of(context).colorScheme.error)),
                    ),
                  // LFPDPPP Art. 8: el registro exige consentimiento explícito
                  // (el backend responde 400 sin `consent:true`).
                  if (_showRegister)
                    CheckboxListTile(
                      value: _consent,
                      controlAffinity: ListTileControlAffinity.leading,
                      contentPadding: EdgeInsets.zero,
                      title: const Text(
                          'Acepto el uso de mis datos (LFPDPPP)'),
                      onChanged: loading
                          ? null
                          : (v) =>
                              setState(() => _consent = v ?? false),
                    ),
                  const SizedBox(height: 16),
                  FilledButton(
                    style: FilledButton.styleFrom(
                        minimumSize: const Size(double.infinity, 48)),
                    onPressed: loading ? null : _submit,
                    child: Text(_showRegister ? 'Crear cuenta' : 'Entrar'),
                  ),
                  TextButton(
                    onPressed: loading
                        ? null
                        : () =>
                            setState(() => _showRegister = !_showRegister),
                    child: Text(_showRegister
                        ? 'Ya tengo cuenta'
                        : 'Crear cuenta nueva'),
                  ),
                  if (!_showRegister)
                    TextButton(
                      onPressed: loading
                          ? null
                          : () => context.go('/recuperar'),
                      child: const Text('Olvidé mi contraseña'),
                    ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }

  void _submit() {
    if (!(_form.currentState?.validate() ?? false)) return;
    final ctrl = ref.read(authControllerProvider.notifier);
    if (_showRegister) {
      if (!_consent) {
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
            content: Text(
                'Debes aceptar el uso de datos para crear tu cuenta.')));
        return;
      }
      ctrl.register(_user.text.trim(), _pass.text, consent: true);
    } else {
      ctrl.login(_user.text.trim(), _pass.text);
    }
  }
}

/// Consentimiento de datos personales (LFPDPPP, contrato §1/§10).
/// Sin registro de consentimiento no se usa telemetría personal.
class ConsentScreen extends ConsumerStatefulWidget {
  const ConsentScreen({super.key});

  @override
  ConsumerState<ConsentScreen> createState() => _ConsentScreenState();
}

class _ConsentScreenState extends ConsumerState<ConsentScreen> {
  /// Consentimiento IA separado (S3): diagnóstico por foto y chat RAG.
  /// Sin esto, la IA responde 403 CONSENT_REQUIRED.
  var _aiConsent = false;

  @override
  Widget build(BuildContext context) {
    final auth = ref.watch(authControllerProvider);
    return Scaffold(
      appBar: AppBar(title: const Text('Privacidad')),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(24),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              const SizedBox(height: 24),
              const Text(
                'Mole.AI usa tus datos (cuenta, plantas, telemetría) para operar '
                'el monitoreo de tu invernadero, conforme a la LFPDPPP. '
                'Puedes revocar este consentimiento cuando quieras desde tu perfil.',
              ),
              if (auth.error != null) ...[
                const SizedBox(height: 8),
                Semantics(
                  liveRegion: true,
                  child: Text(auth.error!,
                      style: TextStyle(
                          color: Theme.of(context).colorScheme.error)),
                ),
                const SizedBox(height: 8),
                OutlinedButton(
                  style: OutlinedButton.styleFrom(
                      minimumSize: const Size(double.infinity, 48)),
                  onPressed: () => ref
                      .read(authControllerProvider.notifier)
                      .logout(),
                  child: const Text('Volver a iniciar sesión'),
                ),
              ],
              const SizedBox(height: 16),
              Semantics(
                label:
                    'Consentimiento para inteligencia artificial: diagnóstico por foto y chat',
                child: CheckboxListTile(
                  value: _aiConsent,
                  onChanged: (v) =>
                      setState(() => _aiConsent = v ?? false),
                  title: const Text(
                      'Acepto el uso de IA en mis diagnósticos y chat'),
                  subtitle: const Text(
                      'Opcional. Sin esto, la IA responde con error y el resto funciona igual.'),
                  controlAffinity: ListTileControlAffinity.leading,
                  contentPadding: EdgeInsets.zero,
                ),
              ),
              const SizedBox(height: 16),
              FilledButton(
                style: FilledButton.styleFrom(
                    minimumSize: const Size(double.infinity, 48)),
                onPressed: () => ref
                    .read(authControllerProvider.notifier)
                    .grantConsent(true, aiConsent: _aiConsent),
                child: const Text('Acepto el uso de mis datos'),
              ),
              const SizedBox(height: 8),
              OutlinedButton(
                style: OutlinedButton.styleFrom(
                    minimumSize: const Size(double.infinity, 48)),
                onPressed: () => ref
                    .read(authControllerProvider.notifier)
                    .grantConsent(false),
                child: const Text('No acepto'),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
