import pytest
from app.config import settings


class TestSettingsFields:
    def test_has_correct_host_port_fields(self):
        assert hasattr(settings, "ms3_host")
        assert hasattr(settings, "ms3_port")
        assert not hasattr(settings, "HOST")
        assert not hasattr(settings, "PORT")

    def test_defaults(self):
        assert settings.ms3_host == "0.0.0.0"
        assert settings.ms3_port == 8003
