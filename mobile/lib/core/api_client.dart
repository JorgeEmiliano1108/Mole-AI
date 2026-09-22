/// Cliente HTTP del contrato móvil (docs/mobile-contract.md §0, §1, §7).
///
/// Reglas implementadas desde el backend real:
/// - baseUrl `API_BASE_URL` (`--dart-define`, default emulador Android) + `/` final.
/// - trailing slash obligatorio en cada path (contrato §0).
/// - `Authorization: Bearer <JWT>` salvo `auth/login/` y `auth/register/`.
/// - 401 → `POST auth/refresh/` UNA vez (salvo en endpoints `auth/*`);
///   si falla → [UnauthorizedException] (la UI va a login).
/// - Timeouts 30s; errores 4xx/5xx/timeout → [ApiException] tipada.
/// - 204 / cuerpo vacío → `{}` (nunca null).
library;

import 'dart:convert';

import 'package:dio/dio.dart';

import 'errors.dart';
import 'session_store.dart';

/// Extrae el `role` del payload de un JWT HS256 sin verificar firma.
///
/// Retorna `user|admin|superuser` si el claim existe y es válido,
/// `null` en cualquier otro caso (token opaco, malformado, sin claim).
/// Uso: sincronizar el rol cacheado tras `auth/refresh/` (RBAC integrity).
/// Fuente de verdad = claim `role` del JWT fresco, no el valor cacheado.
String? roleFromJwt(String token) {
  try {
    final parts = token.split('.');
    if (parts.length != 3) return null;
    final payload = json.decode(
      utf8.decode(base64Url.decode(base64Url.normalize(parts[1]))),
    );
    if (payload is! Map) return null;
    final role = payload['role'];
    if (role == 'user' || role == 'admin' || role == 'superuser') {
      return role as String;
    }
    return null;
  } catch (_) {
    return null;
  }
}

class ApiClient {
  ApiClient._(this._session, this._dio, String? baseUrl) {
    _dio.options = BaseOptions(
      baseUrl: withSlash(
        baseUrl ??
            const String.fromEnvironment(
              'API_BASE_URL',
              defaultValue: 'http://10.0.2.2:8000/api/v1/',
            ),
      ),
      connectTimeout: const Duration(seconds: 30),
      receiveTimeout: const Duration(seconds: 30),
      sendTimeout: const Duration(seconds: 30),
      contentType: 'application/json',
      responseType: ResponseType.json,
    );
    _dio.interceptors.add(
      InterceptorsWrapper(
        onRequest: (opts, handler) async {
          final enforce = opts.extra['enforceSlash'] != false;
          opts.path = normalizePath(opts.path, enforceSlash: enforce);
          if (!_isPublicAuth(opts.path)) {
            final token = await _session.readToken();
            if (token != null && token.isNotEmpty) {
              opts.headers['Authorization'] = 'Bearer $token';
            }
          }
          handler.next(opts);
        },
        onError: (err, handler) async {
          final req = err.requestOptions;
          if (err.response?.statusCode == 401 &&
              req.extra['retried'] != true &&
              !_isAuthPath(req.path)) {
            if (await _tryRefresh()) {
              req.extra['retried'] = true;
              req.headers['Authorization'] =
                  'Bearer ${await _session.readToken()}';
              try {
                final resp = await _dio.fetch<Map<String, dynamic>>(req);
                return handler.resolve(resp);
              } on DioException catch (e) {
                return handler.next(_mapError(e));
              }
            }
          }
          handler.next(_mapError(err));
        },
      ),
    );
  }

  factory ApiClient(
          {required SessionStore session, Dio? dio, String? baseUrl}) =>
      ApiClient._(session, dio ?? Dio(), baseUrl);

  /// Normaliza un path al contrato: `/` final salvo que la ruta del backend
  /// sea exacta sin slash (ej. MS3 `/api/v1/reports/generate`).
  /// `enforceSlash:false` la deja intacta.
  static String normalizePath(String path, {bool enforceSlash = true}) {
    if (!enforceSlash || path.endsWith('/')) return path;
    return '$path/';
  }

  final SessionStore _session;
  final Dio _dio;

  /// Endpoints que nunca llevan Bearer (login/register crean la sesión).
  static bool _isPublicAuth(String path) =>
      path.endsWith('auth/login/') ||
      path.endsWith('auth/register/') ||
      path.endsWith('auth/password-reset/request/') ||
      path.endsWith('auth/password-reset/confirm/') ||
      // Portal público (issue 14): catálogo, clima y ping sin sesión.
      path.contains('plants/search/') ||
      path.contains('plants/species/') ||
      path.contains('weather/') ||
      path.endsWith('health/');

  /// Endpoints `auth/*`: el refresh no aplica (evita bucle 401→refresh→401).
  static bool _isAuthPath(String path) => path.contains('auth/');

  /// Garantiza `/` final (contrato §0). Ver [normalizePath].
  static String withSlash(String path) =>
      normalizePath(path, enforceSlash: true);

  Future<bool> _tryRefresh() async {
    try {
      final resp = await _dio.post<Map<String, dynamic>>('auth/refresh/');
      final token = resp.data?['token'];
      if (token is String && token.isNotEmpty) {
        // RBAC integrity: el rol se sincroniza desde el JWT fresco
        // (claim `role`), no del caché. Orden: campo explícito del
        // backend (si existe) > claim del JWT > valor cacheado.
        final explicitRole = resp.data?['role'];
        final freshRole = (explicitRole is String &&
                (explicitRole == 'user' ||
                    explicitRole == 'admin' ||
                    explicitRole == 'superuser'))
            ? explicitRole
            : roleFromJwt(token);
        final role = freshRole ?? await _session.readRole() ?? 'user';
        await _session.writeToken(token, role);
        return true;
      }
      return false;
    } catch (_) {
      return false;
    }
  }

  DioException _mapError(DioException err) {
    final status = err.response?.statusCode;
    if (err.type == DioExceptionType.connectionTimeout ||
        err.type == DioExceptionType.receiveTimeout ||
        err.type == DioExceptionType.sendTimeout) {
      return DioException(
        requestOptions: err.requestOptions,
        error: RetryableException('Sin respuesta del servidor. Revisa tu conexión.'),
      );
    }
    if (status == null) {
      return DioException(
        requestOptions: err.requestOptions,
        error: RetryableException('Sin conexión con el servidor.'),
      );
    }
    return DioException(
      requestOptions: err.requestOptions,
      response: err.response,
      error: apiExceptionFromStatus(status, err.response?.data),
    );
  }

  /// GET tipado a objeto. Lanza [ApiException].
  Future<Map<String, dynamic>> getJson(String path,
      {Map<String, dynamic>? query, bool enforceSlash = true}) async {
    try {
      final resp = await _dio.get<Map<String, dynamic>>(path,
          queryParameters: query,
          options: Options(extra: {'enforceSlash': enforceSlash}));
      return _bodyOrEmpty(resp);
    } on DioException catch (e) {
      throw _unwrap(e);
    }
  }

  /// GET tipado a lista (ej. `plants/search/`, `my-collection/`: el backend
  /// devuelve array directo, no envelope). Lanza [ApiException].
  Future<List<dynamic>> getList(String path,
      {Map<String, dynamic>? query, bool enforceSlash = true}) async {
    try {
      final resp = await _dio.get<List<dynamic>>(path,
          queryParameters: query,
          options: Options(extra: {'enforceSlash': enforceSlash}));
      return resp.data ?? [];
    } on DioException catch (e) {
      throw _unwrap(e);
    }
  }

  static ApiException _unwrap(DioException e) => e.error is ApiException
      ? e.error! as ApiException
      : ApiException('Error de red.', details: e.message);

  /// PATCH JSON tipado. Lanza [ApiException].
  Future<Map<String, dynamic>> patchJson(String path,
      {Object? data, bool enforceSlash = true}) async {
    try {
      final resp = await _dio.patch<Map<String, dynamic>>(
        path,
        data: data,
        options: Options(extra: {'enforceSlash': enforceSlash}),
      );
      return _bodyOrEmpty(resp);
    } on DioException catch (e) {
      throw _unwrap(e);
    }
  }

  /// DELETE tipado (204 vacío → `{}`). Lanza [ApiException].
  /// 204 sin cuerpo no se parsea como JSON (evita cast roto de Dio).
  Future<Map<String, dynamic>> deleteJson(String path,
      {bool enforceSlash = true}) async {
    try {
      final resp = await _dio.delete<dynamic>(path,
          options: Options(extra: {'enforceSlash': enforceSlash}));
      if (resp.statusCode == 204 || resp.data == null) return {};
      final data = resp.data;
      if (data is Map<String, dynamic>) return data;
      return {};
    } on DioException catch (e) {
      throw _unwrap(e);
    }
  }

  /// POST JSON tipado. Lanza [ApiException].
  Future<Map<String, dynamic>> postJson(String path,
      {Object? data,
      Duration? receiveTimeout,
      Map<String, dynamic>? query,
      bool enforceSlash = true}) async {
    try {
      final resp = await _dio.post<Map<String, dynamic>>(
        path,
        data: data,
        queryParameters: query,
        options: Options(
          receiveTimeout: receiveTimeout,
          extra: {'enforceSlash': enforceSlash},
        ),
      );
      return _bodyOrEmpty(resp);
    } on DioException catch (e) {
      throw _unwrap(e);
    }
  }

  /// POST multipart (diagnóstico por foto). Timeout IA 120s (contrato §0).
  Future<Map<String, dynamic>> postMultipart(String path, FormData data) {
    return postJson(path,
        data: data, receiveTimeout: const Duration(seconds: 120));
  }

  /// Ping pre-login (contrato §5b, endpoint público).
  Future<bool> ping() async {
    try {
      final body = await getJson('health/');
      return body['status'] == 'healthy';
    } catch (_) {
      return false;
    }
  }

  static Map<String, dynamic> _bodyOrEmpty(
      Response<Map<String, dynamic>> resp) {
    final data = resp.data;
    if (data == null) return {};
    return Map<String, dynamic>.from(data);
  }
}
