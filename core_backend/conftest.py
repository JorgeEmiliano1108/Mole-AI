import pytest
from django.core.cache import cache


@pytest.fixture(autouse=True)
def _clear_cache_between_tests():
    """Limpia la caché de Django/DRF entre tests para aislar throttling."""
    cache.clear()
    yield
    cache.clear()
