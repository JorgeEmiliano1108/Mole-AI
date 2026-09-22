/// Errores tipados del contrato móvil (docs/mobile-contract.md §7).
///
/// Mapea códigos HTTP a excepciones que la UI puede manejar sin adivinar:
/// reintentar (502/503/timeout), re-login (401 agotado), backoff (429),
/// mostrar mensaje (resto). Nunca se expone el JWT ni detalles internos.
library;

/// Error base de API.
class ApiException implements Exception {
  ApiException(this.message, {this.statusCode, this.details});

  /// Mensaje seguro para UI (viene del backend o es genérico).
  final String message;
  final int? statusCode;
  final Object? details;

  @override
  String toString() => 'ApiException($statusCode): $message';
}

/// 401 incluso tras intentar refresh: la sesión murió → ir a login.
class UnauthorizedException extends ApiException {
  UnauthorizedException([super.message = 'Sesión expirada. Inicia sesión de nuevo.'])
      : super(statusCode: 401);
}

/// 429: throttle del gateway → backoff exponencial, no reintento inmediato.
class RateLimitedException extends ApiException {
  RateLimitedException([super.message = 'Demasiadas peticiones. Espera un momento.'])
      : super(statusCode: 429);
}

/// 502/503/timeout: reintentable una vez (solo GET / polling).
class RetryableException extends ApiException {
  RetryableException(super.message, {super.statusCode, super.details});
}

/// Construye la excepción adecuada desde un status HTTP + cuerpo.
ApiException apiExceptionFromStatus(int? status, dynamic data) {
  final msg = _messageFrom(data);
  switch (status) {
    case 401:
      return UnauthorizedException(msg);
    case 429:
      return RateLimitedException(msg);
    case 502:
    case 503:
    case 504:
      return RetryableException(msg, statusCode: status);
    default:
      return ApiException(msg, statusCode: status, details: data);
  }
}

String _messageFrom(dynamic data) {
  if (data is Map) {
    for (final k in const ['error', 'message', 'detail']) {
      final v = data[k];
      if (v is String && v.isNotEmpty) return v;
    }
  }
  return 'Error inesperado. Intenta de nuevo.';
}
