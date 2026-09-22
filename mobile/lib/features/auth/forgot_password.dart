/// Recuperación de contraseña (ADR-0006, issue 14).
///
/// Request siempre responde 202 (anti-enumeración): la UI dice lo mismo
/// exista o no la cuenta. Confirm con token de un solo uso TTL 1h.
library;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import 'package:mole_ai/core/errors.dart';
import 'package:mole_ai/features/auth/auth_controller.dart'
    show authRepositoryProvider;

String? _required(String? v) =>
    v == null || v.trim().isEmpty ? 'Requerido' : null;

String _friendly(Object e) => e is ApiException
    ? e.message
    : 'Error inesperado. Intenta de nuevo.';

class ForgotRequestScreen extends ConsumerStatefulWidget {
  const ForgotRequestScreen({super.key});

  @override
  ConsumerState<ForgotRequestScreen> createState() =>
      _ForgotRequestScreenState();
}

class _ForgotRequestScreenState extends ConsumerState<ForgotRequestScreen> {
  final _form = GlobalKey<FormState>();
  final _email = TextEditingController();
  bool _loading = false;
  bool _sent = false;
  String? _error;

  @override
  void dispose() {
    _email.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    if (!(_form.currentState?.validate() ?? false)) return;
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      await ref
          .read(authRepositoryProvider)
          .requestPasswordReset(_email.text.trim());
      if (mounted) setState(() => _sent = true);
    } catch (e) {
      if (mounted) setState(() => _error = _friendly(e));
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Recuperar contraseña')),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(24),
          child: _sent
              ? Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    const Text(
                        'Si la cuenta existe, enviamos un enlace válido por '
                        '1 hora. Revisa tu correo (y spam).'),
                    const SizedBox(height: 16),
                    OutlinedButton(
                      onPressed: () => context.go('/login'),
                      child: const Text('Volver a entrar'),
                    ),
                  ],
                )
              : Form(
                  key: _form,
                  child: AutofillGroup(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.stretch,
                      children: [
                        const Text(
                            'Escribe tu correo y te enviaremos un enlace '
                            'para crear una contraseña nueva.'),
                        const SizedBox(height: 16),
                        TextFormField(
                          controller: _email,
                          decoration: const InputDecoration(
                              labelText: 'Correo'),
                          keyboardType: TextInputType.emailAddress,
                          autofillHints: const [AutofillHints.email],
                          textInputAction: TextInputAction.done,
                          enabled: !_loading,
                          validator: _required,
                          onFieldSubmitted: (_) => _submit(),
                        ),
                        const SizedBox(height: 8),
                        if (_error != null)
                          Semantics(
                            liveRegion: true,
                            child: Text(_error!,
                                style: TextStyle(
                                    color: Theme.of(context)
                                        .colorScheme
                                        .error)),
                          ),
                        const SizedBox(height: 16),
                        FilledButton(
                          style: FilledButton.styleFrom(
                              minimumSize:
                                  const Size(double.infinity, 48)),
                          onPressed: _loading ? null : _submit,
                          child: const Text('Enviar enlace'),
                        ),
                      ],
                    ),
                  ),
                ),
        ),
      ),
    );
  }
}

class ForgotConfirmScreen extends ConsumerStatefulWidget {
  /// Token desde `?token=` (deep-link del correo) o pegado manual.
  const ForgotConfirmScreen({super.key, this.token});

  final String? token;

  @override
  ConsumerState<ForgotConfirmScreen> createState() =>
      _ForgotConfirmScreenState();
}

class _ForgotConfirmScreenState extends ConsumerState<ForgotConfirmScreen> {
  final _form = GlobalKey<FormState>();
  late final TextEditingController _token;
  final _pass = TextEditingController();
  bool _loading = false;
  bool _done = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    _token = TextEditingController(text: widget.token ?? '');
  }

  @override
  void dispose() {
    _token.dispose();
    _pass.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    if (!(_form.currentState?.validate() ?? false)) return;
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      await ref.read(authRepositoryProvider).confirmPasswordReset(
          _token.text.trim(), _pass.text);
      if (mounted) setState(() => _done = true);
    } catch (e) {
      if (mounted) setState(() => _error = _friendly(e));
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Nueva contraseña')),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(24),
          child: _done
              ? Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    const Text(
                        'Contraseña actualizada. Entra con la nueva.'),
                    const SizedBox(height: 16),
                    FilledButton(
                      onPressed: () => context.go('/login'),
                      child: const Text('Entrar'),
                    ),
                  ],
                )
              : Form(
                  key: _form,
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                      TextFormField(
                        controller: _token,
                        decoration: const InputDecoration(
                            labelText: 'Token del correo'),
                        enabled: !_loading,
                        validator: _required,
                      ),
                      const SizedBox(height: 12),
                      TextFormField(
                        controller: _pass,
                        decoration: const InputDecoration(
                            labelText: 'Contraseña nueva'),
                        obscureText: true,
                        enableSuggestions: false,
                        autocorrect: false,
                        autofillHints: const [
                          AutofillHints.newPassword
                        ],
                        textInputAction: TextInputAction.done,
                        enabled: !_loading,
                        validator: (v) {
                          if (_required(v) != null) return 'Requerido';
                          if (v!.length < 6) return 'Mínimo 6 caracteres';
                          return null;
                        },
                        onFieldSubmitted: (_) => _submit(),
                      ),
                      const SizedBox(height: 8),
                      if (_error != null)
                        Semantics(
                          liveRegion: true,
                          child: Text(_error!,
                              style: TextStyle(
                                  color: Theme.of(context)
                                      .colorScheme
                                      .error)),
                        ),
                      const SizedBox(height: 16),
                      FilledButton(
                        style: FilledButton.styleFrom(
                            minimumSize:
                                const Size(double.infinity, 48)),
                        onPressed: _loading ? null : _submit,
                        child: const Text('Guardar contraseña'),
                      ),
                    ],
                  ),
                ),
        ),
      ),
    );
  }
}
