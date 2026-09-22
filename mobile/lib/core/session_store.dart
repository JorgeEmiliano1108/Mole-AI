/// Almacén de sesión: UNA sola key de token (cierra deuda dual-key web
/// `mole_jwt`+`moleia_token`). Token en secure storage, prefs no sensibles aparte.
library;

import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:shared_preferences/shared_preferences.dart';

/// Contrato de sesión (inyectable para tests).
abstract class SessionStore {
  Future<String?> readToken();
  Future<void> writeToken(String token, String role);
  Future<String?> readRole();
  Future<void> clear();
  Future<String?> readDeviceId();
  Future<void> writeDeviceId(String id);
}

/// Implementación productiva.
class SecureSessionStore implements SessionStore {
  SecureSessionStore._(this._secure, this._prefs);

  factory SecureSessionStore(
          {FlutterSecureStorage? secure, SharedPreferences? prefs}) =>
      SecureSessionStore._(
          secure ?? const FlutterSecureStorage(), prefs);

  static const _kToken = 'mole_jwt';
  static const _kRole = 'mole_role';
  static const _kDeviceId = 'mole_device_id';

  final FlutterSecureStorage _secure;
  SharedPreferences? _prefs;

  Future<SharedPreferences> get _sp async =>
      _prefs ??= await SharedPreferences.getInstance();

  @override
  Future<String?> readToken() => _secure.read(key: _kToken);

  @override
  Future<void> writeToken(String token, String role) async {
    await _secure.write(key: _kToken, value: token);
    await _secure.write(key: _kRole, value: role);
  }

  @override
  Future<String?> readRole() => _secure.read(key: _kRole);

  @override
  Future<void> clear() async {
    await _secure.delete(key: _kToken);
    await _secure.delete(key: _kRole);
  }

  @override
  Future<String?> readDeviceId() async =>
      (await _sp).getString(_kDeviceId);

  @override
  Future<void> writeDeviceId(String id) async =>
      (await _sp).setString(_kDeviceId, id);
}

/// Implementación en memoria para tests (sin platform channels).
class MemorySessionStore implements SessionStore {
  String? token;
  String? role;
  String? deviceId;

  @override
  Future<String?> readToken() async => token;

  @override
  Future<void> writeToken(String t, String r) async {
    token = t;
    role = r;
  }

  @override
  Future<String?> readRole() async => role;

  @override
  Future<void> clear() async {
    token = null;
    role = null;
  }

  @override
  Future<String?> readDeviceId() async => deviceId;

  @override
  Future<void> writeDeviceId(String id) async => deviceId = id;
}
