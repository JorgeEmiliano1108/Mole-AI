import pytest
from django.conf import settings

def test_security_middleware_order():
    # NOTA: django-prometheus NO está instalado (ver requirements.txt);
    # el stack real es Cors → … → JwtHttp → Axes → GracefulDegradation.
    assert settings.MIDDLEWARE[0] == 'corsheaders.middleware.CorsMiddleware'
    assert settings.MIDDLEWARE[-1] == (
        'mole_ai_backend.middleware.error_handling.GracefulDegradationMiddleware'
    )
    assert 'apps.authentication.middleware.JwtHttpMiddleware' in settings.MIDDLEWARE
    assert 'axes.middleware.AxesMiddleware' in settings.MIDDLEWARE
