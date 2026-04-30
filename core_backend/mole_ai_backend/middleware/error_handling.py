# =============================================================================
# Copyright (C) 2024-2026 Mole.AI — All Rights Reserved.
# =============================================================================
import logging
from django.http import JsonResponse
import requests
import redis

logger = logging.getLogger(__name__)


class GracefulDegradationMiddleware:
    """
    Middleware that intercepts unhandled exceptions to prevent the API from
    crashing and exposing stack traces during MS1/MS2/MinIO/Redis outages.
    Returns a standardized 503 Service Unavailable JSON response instead.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_exception(self, request, exception):
        # Catch network, timeout, and connection errors from external services
        is_connection_error = (
            isinstance(exception, requests.exceptions.RequestException) or
            isinstance(exception, redis.exceptions.RedisError) or
            exception.__class__.__name__ in (
                'ConnectionError', 'TimeoutError', 'Timeout', 
                'MoleAIServiceError', 'ClientError', 'ConnectionRefusedError'
            )
        )

        if is_connection_error:
            logger.warning(
                "graceful_degradation_triggered",
                extra={
                    "error_type": exception.__class__.__name__,
                    "error_msg": str(exception),
                    "path": request.path
                }
            )
            return JsonResponse(
                {
                    "error": "SERVICE_UNAVAILABLE",
                    "message": "El servicio de IA está temporalmente fuera de línea.",
                    "status": "degraded"
                },
                status=503
            )
        
        # For other exceptions, return None to let Django's default exception handler handle it
        return None
