/// Repositorio de autenticación (contrato §1).
///
/// Endpoints: `POST auth/login|register|refresh|logout|consent`,
/// `GET/PATCH auth/profile`. Guarda UNA key (`mole_jwt`) + rol.
library;

import 'package:mole_ai/core/api_client.dart';
import 'package:mole_ai/core/session_store.dart';

class AuthRepository {
  AuthRepository(this._api, this._session);

  final ApiClient _api;
  final SessionStore _session;

  /// Login con username o email (`@` resuelve por email en backend).
  /// Retorna el rol (`user|admin|superuser`).
  Future<String> login(String identifier, String password) async {
    final body = await _api.postJson('auth/login/', data: {
      'username': identifier,
      'password': password,
    });
    final token = body['token'] as String;
    final role = (body['role'] as String?) ?? 'user';
    await _session.writeToken(token, role);
    return role;
  }

  Future<void> register(String username, String password,
      {String? email, bool consent = false}) async {
    await _api.postJson('auth/register/', data: {
      'username': username,
      'password': password,
      if (email != null && email.isNotEmpty) 'email': email,
      // LFPDPPP Art. 8: el backend exige consentimiento explícito (400 si no).
      'consent': consent,
    });
  }

  /// Logout stateless: avisa al backend (best-effort) y borra la sesión local.
  Future<void> logout() async {
    try {
      await _api.postJson('auth/logout/');
    } catch (_) {
      // Best-effort: la sesión local se borra igual.
    }
    await _session.clear();
  }

  Future<Map<String, dynamic>> profile() => _api.getJson('auth/profile/');

  /// ADR-0006: solicita correo de recuperación. Siempre 202
  /// (anti-enumeración: el backend no revela si el email existe).
  Future<void> requestPasswordReset(String email) async {
    await _api.postJson('auth/password-reset/request/', data: {
      'email': email.trim(),
    });
  }

  /// ADR-0006: confirma con token de un solo uso TTL 1h + password NIST.
  Future<void> confirmPasswordReset(String token, String newPassword) async {
    await _api.postJson('auth/password-reset/confirm/', data: {
      'token': token.trim(),
      'new_password': newPassword,
    });
  }

  /// ARCO: anonimiza y borra la cuenta (204). Usado en teardown E2E.
  Future<void> deleteProfile() async {
    await _api.deleteJson('auth/profile/');
  }

  /// Sliding window (contrato §1): exige Bearer vigente; el backend rota `jti`.
  /// Lanza [UnauthorizedException] si el token ya expiró → re-login.
  /// RBAC integrity: el rol cacheado se sincroniza desde el JWT fresco.
  Future<void> refresh() async {
    final body = await _api.postJson('auth/refresh/');
    final token = body['token'] as String;
    final explicitRole = body['role'];
    final freshRole = (explicitRole is String &&
            (explicitRole == 'user' ||
                explicitRole == 'admin' ||
                explicitRole == 'superuser'))
        ? explicitRole
        : roleFromJwt(token);
    final role = freshRole ?? await _session.readRole() ?? 'user';
    await _session.writeToken(token, role);
  }

  /// Consentimiento LFPDPPP. `granted=true` registra CONSENT_GRANTED (+AuditLog).
  Future<Map<String, dynamic>> setConsent(bool granted) =>
      _api.postJson('auth/consent/', data: {'consent': granted});

  Future<bool> hasConsented() async {
    try {
      final p = await profile();
      return p['data_consent'] == true;
    } catch (_) {
      return false;
    }
  }
}
