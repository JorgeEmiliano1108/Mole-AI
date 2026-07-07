import pytest
from django.conf import settings

def test_prometheus_middleware_is_first():
    first = settings.MIDDLEWARE[0]
    assert 'PrometheusBeforeMiddleware' in first
