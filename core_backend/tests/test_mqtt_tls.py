"""
Mole.AI - Sprint 1: MQTT TLS Red Phase Tests
Objetivo: Verificar que el broker MQTT requiere TLS en puerto 8883 y rechaza conexiones en 1883.
Metodología: TDD Red-Green-Refactor
"""

import pytest
import ssl
import time
from paho.mqtt.client import Client as MQTTClient
from paho.mqtt.enums import CallbackAPIVersion


# Configuración de certificados (ruta DENTRO del contenedor django-backend)
CERTS_DIR = "/app/mqtt_certs"  # Volumen montado en docker-compose.yml
CA_CERT = f"{CERTS_DIR}/ca.crt"
SERVER_CERT = f"{CERTS_DIR}/server.crt"
SERVER_KEY = f"{CERTS_DIR}/server.key"

# Docker service name for MQTT broker
MQTT_BROKER_HOST = "mqtt_broker"


class TestMqttTlsRedPhase:
    """
    Fase RED: Tests que deben FALLAR porque aún no existe:
    1. Listener 8883 con TLS configurado
    2. Rechazo de conexiones en 1883 (o cierre del puerto)
    """

    def test_1883_without_tls_should_fail_or_reject(self):
        """
        Test: Conectar a puerto 1883 sin TLS debe FALLAR o ser RECHAZADO.
        Comportamiento deseado: El puerto 1883 no debe aceptar conexiones (o debe estar cerrado).
        Fase RED: Este test FALLA porque actualmente 1883 acepta conexiones sin TLS.
        """
        client = MQTTClient(callback_api_version=CallbackAPIVersion.VERSION2)
        
        # Callback para capturar resultado
        connection_result = {"connected": False, "rc": None}
        
        def on_connect(client, userdata, flags, rc, properties=None):
            connection_result["connected"] = (rc == 0)
            connection_result["rc"] = rc
        
        client.on_connect = on_connect
        
        try:
            client.connect("localhost", 1883, 5)
            client.loop_start()
            time.sleep(2)  # Esperar conexión
            client.loop_stop()
            client.disconnect()
        except Exception as e:
            connection_result["error"] = str(e)
        
        # En fase RED: 1883 actualmente FUNCIONA (test falla porque esperamos fallo)
        # Después de implementar: 1883 debe rechazar → test PASARÁ
        assert not connection_result.get("connected", True), \
            f"ERROR: Puerto 1883 acepta conexiones sin TLS. Debe rechazar. RC={connection_result.get('rc')}"


    def test_8883_with_tls_should_succeed(self):
        """
        Test: Conectar a puerto 8883 con certificados TLS debe EXITOSAMENTE.
        Comportamiento deseado: El puerto 8883 acepta conexiones con TLS válido.
        Fase GREEN: Este test debe PASAR porque 8883 está configurado con TLS.
        """
        client = MQTTClient(callback_api_version=CallbackAPIVersion.VERSION2)
        
        # Configurar TLS con certificados montados en /app/mqtt_certs
        try:
            client.tls_set(
                ca_certs=CA_CERT,
                certfile=None,
                keyfile=None,
                tls_version=ssl.PROTOCOL_TLS_CLIENT
            )
        except FileNotFoundError as e:
            pytest.fail(f"GREEM Phase: Certificado CA no encontrado en {CA_CERT}. Error: {str(e)}")
        
        connection_result = {"connected": False, "rc": None}
        
        def on_connect(client, userdata, flags, rc, properties=None):
            connection_result["connected"] = (rc == 0)
            connection_result["rc"] = rc
        
        client.on_connect = on_connect
        
        try:
            # Usar nombre del servicio Docker, no localhost
            broker_host = globals().get("MQTT_BROKER_HOST", "mqtt_broker")
            client.connect(broker_host, 8883, 5)
            client.loop_start()
            time.sleep(2)
            client.loop_stop()
            client.disconnect()
        except Exception as e:
            pytest.fail(f"GREEM Phase: No se pudo conectar a 8883. Error: {str(e)}")
        
        # En fase GREEN: 8883 con TLS debe aceptar conexión
        assert connection_result.get("connected", False), \
            f"ERROR: Puerto 8883 con TLS no funciona. RC={connection_result.get('rc')}"


    def test_1883_clearsk_text_traffic_rejected(self):
        """
        Test adicional: Verificar que el tráfico en claro (sin cifrar) en 1883 es rechazado.
        Fase RED: Actualmente 1883 acepta tráfico en claro → test FALLA.
        """
        client = MQTTClient(callback_api_version=CallbackAPIVersion.VERSION2)
        messages = []
        
        def on_connect(client, userdata, flags, rc, properties=None):
            if rc == 0:
                client.subscribe("test/topic", qos=1)
        
        def on_message(client, userdata, msg):
            messages.append(msg.payload.decode())
        
        client.on_connect = on_connect
        client.on_message = on_message
        
        try:
            client.connect("localhost", 1883, 5)
            client.loop_start()
            time.sleep(1)
            client.publish("test/topic", "unencrypted_data", qos=1)
            time.sleep(1)
            client.loop_stop()
            client.disconnect()
        except:
            pass
        
        # En fase RED: 1883 actualmente acepta tráfico → test FALLA
        assert len(messages) == 0, \
            "ERROR: Puerto 1883 acepta tráfico en claro. Debe rechazar."


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
