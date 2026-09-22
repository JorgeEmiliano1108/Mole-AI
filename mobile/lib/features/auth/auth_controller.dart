/// Controlador de sesión con Riverpod (contrato §1).
///
/// Estados: loading → unauthenticated | needsConsent | authenticated.
/// El refresh de JWT lo hace el interceptor de [ApiClient]; aquí solo se
/// reacciona a [UnauthorizedException] volviendo a login.
library;

import 'dart:async';

import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'package:mole_ai/core/api_client.dart';
import 'package:mole_ai/core/errors.dart';
import 'package:mole_ai/core/session_store.dart';
import 'auth_repository.dart';

enum AuthStatus { loading, unauthenticated, needsConsent, authenticated }

class AuthState {
  const AuthState({required this.status, this.role, this.error});
  final AuthStatus status;
  final String? role;
  final String? error;

  /// Gate admin (issue 15): drawer muestra sección admin solo con rol.
  bool get isAdmin => role == 'admin' || role == 'superuser';
  bool get isAuthenticated =>
      status == AuthStatus.authenticated || status == AuthStatus.needsConsent;

  AuthState copyWith({AuthStatus? status, String? role, String? error}) =>
      AuthState(
        status: status ?? this.status,
        role: role ?? this.role,
        error: error,
      );
}

final sessionStoreProvider =
    Provider<SessionStore>((_) => SecureSessionStore());

final apiClientProvider = Provider<ApiClient>(
    (ref) => ApiClient(session: ref.watch(sessionStoreProvider)));

final authRepositoryProvider = Provider<AuthRepository>((ref) => AuthRepository(
    ref.watch(apiClientProvider), ref.watch(sessionStoreProvider)));

final authControllerProvider =
    NotifierProvider<AuthController, AuthState>(AuthController.new);

class AuthController extends Notifier<AuthState> {
  /// Refresh proactivo (contrato §1: TTL 20min): renueva al min 15 en
  /// segundo plano para no interrumpir al usuario en campo.
  static const _refreshAt = Duration(minutes: 15);
  Timer? _refreshTimer;

  @override
  AuthState build() {
    ref.onDispose(() => _refreshTimer?.cancel());
    Future.microtask(restore);
    return const AuthState(status: AuthStatus.loading);
  }

  void _scheduleRefresh() {
    _refreshTimer?.cancel();
    _refreshTimer = Timer(_refreshAt, () async {
      try {
        await _repo.refresh();
        _scheduleRefresh();
      } on UnauthorizedException {
        await ref.read(sessionStoreProvider).clear();
        state = const AuthState(status: AuthStatus.unauthenticated);
      } catch (_) {
        // Sin red u otro fallo: reintenta en el siguiente ciclo.
        _scheduleRefresh();
      }
    });
  }

  void _cancelRefresh() {
    _refreshTimer?.cancel();
    _refreshTimer = null;
  }

  AuthRepository get _repo => ref.read(authRepositoryProvider);

  Future<void> restore() async {
    final store = ref.read(sessionStoreProvider);
    final token = await store.readToken();
    if (token == null || token.isEmpty) {
      state = const AuthState(status: AuthStatus.unauthenticated);
      return;
    }
    try {
      final consented = await _repo.hasConsented();
      final authenticated = consented;
      state = AuthState(
        status:
            authenticated ? AuthStatus.authenticated : AuthStatus.needsConsent,
        role: await store.readRole(),
      );
      if (authenticated) {
        _scheduleRefresh();
      } else {
        _cancelRefresh();
      }
    } on UnauthorizedException {
      await store.clear();
      _cancelRefresh();
      state = const AuthState(status: AuthStatus.unauthenticated);
    } catch (e) {
      // Sin red: si hay token, se entra; el interceptor reintentará luego.
      state = AuthState(
        status: AuthStatus.authenticated,
        role: await store.readRole(),
        error: e is ApiException ? e.message : null,
      );
      _scheduleRefresh();
    }
  }

  Future<void> login(String identifier, String password) async {
    state = const AuthState(status: AuthStatus.loading);
    try {
      final role = await _repo.login(identifier, password);
      final consented = await _repo.hasConsented();
      final authenticated = consented;
      state = AuthState(
        status:
            authenticated ? AuthStatus.authenticated : AuthStatus.needsConsent,
        role: role,
      );
      if (authenticated) {
        _scheduleRefresh();
      }
    } on ApiException catch (e) {
      state = AuthState(status: AuthStatus.unauthenticated, error: e.message);
    }
  }

  Future<void> register(String username, String password,
      {String? email, bool consent = false}) async {
    state = const AuthState(status: AuthStatus.loading);
    try {
      await _repo.register(username, password,
          email: email, consent: consent);
      // Tras registro (requiere verificación de email), se pide login.
      state = const AuthState(status: AuthStatus.unauthenticated);
    } on ApiException catch (e) {
      state = AuthState(status: AuthStatus.unauthenticated, error: e.message);
    }
  }

  Future<void> grantConsent(bool granted) async {
    try {
      await _repo.setConsent(granted);
      final store = ref.read(sessionStoreProvider);
      state = AuthState(
        status: AuthStatus.authenticated,
        role: await store.readRole(),
      );
      _scheduleRefresh();
    } on ApiException catch (e) {
      state = state.copyWith(error: e.message);
    }
  }

  Future<void> logout() async {
    _cancelRefresh();
    await _repo.logout();
    state = const AuthState(status: AuthStatus.unauthenticated);
  }
}
