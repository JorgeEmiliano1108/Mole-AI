"""Resiliencia del listener MQTT (TD-MQTT): caída del broker sin crash.

Broker inalcanzable → mensaje ERROR controlado, sin excepción propagada.
"""
from io import StringIO
from unittest.mock import patch

import pytest
from django.core.management import call_command


@pytest.mark.django_db
def test_mqtt_broker_caido_no_revienta(monkeypatch):
    monkeypatch.setenv("DJANGO_MQTT_SECRET", "test-secret")
    monkeypatch.setenv("MQTT_BROKER_URI", "mqtt://127.0.0.1:9")
    monkeypatch.setenv("MQTT_TLS_ENABLED", "False")

    def _boom(*args, **kwargs):
        raise ConnectionRefusedError("broker caído")

    out = StringIO()
    with patch(
        "apps.core.management.commands.mqtt_listener.mqtt.Client"
    ) as mock_client_cls:
        mock_client_cls.return_value.connect.side_effect = _boom
        call_command("mqtt_listener", stdout=out)
    assert "Error fatal" in out.getvalue()
