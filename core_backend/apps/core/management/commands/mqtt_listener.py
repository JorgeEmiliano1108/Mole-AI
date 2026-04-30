import os
import json
import logging
import urllib.parse
from django.core.management.base import BaseCommand
from django.db import transaction
from django.conf import settings
import paho.mqtt.client as mqtt

from apps.core.serializers import SensorBatchReadingSerializer
from apps.core.models import SensorLog

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Inicia el daemon consumidor MQTT para Mole.AI'

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self.stdout.write(self.style.SUCCESS("Conectado exitosamente al Broker MQTT."))
            # Suscripción con QoS 1 al topic del ESP32
            client.subscribe("mole/node/telemetry", qos=1)
            self.stdout.write(self.style.SUCCESS("Suscrito al topic: mole/node/telemetry (QoS 1)"))
        else:
            self.stdout.write(self.style.ERROR(f"Error al conectar con código: {rc}"))

    def on_message(self, client, userdata, msg):
        try:
            payload_str = msg.payload.decode('utf-8')
            payload = json.loads(payload_str)
            
            # Usar SensorBatchReadingSerializer para validar la lectura individual
            serializer = SensorBatchReadingSerializer(data=payload)
            if serializer.is_valid():
                with transaction.atomic():
                    # Crear el registro en PostgreSQL
                    SensorLog.objects.create(**serializer.validated_data)
                logger.info(f"Telemetría persistida correctamente (plant_id: {payload.get('plant_id')})")
            else:
                logger.error(f"Payload MQTT rechazado (Validación): {serializer.errors}")
        except json.JSONDecodeError:
            logger.error(f"Error: JSON malformado recibido en topic {msg.topic}")
        except Exception as e:
            logger.exception("Excepción crítica al procesar el mensaje MQTT")

    def handle(self, *args, **options):
        broker_uri = os.getenv('CONFIG_MQTT_BROKER_URI', 'mqtt://127.0.0.1:1883')
        hardware_key = os.getenv('DJANGO_MQTT_SECRET')

        if not hardware_key:
            self.stdout.write(self.style.ERROR("FATAL: DJANGO_MQTT_SECRET no encontrada en el entorno."))
            return

        # Parsear la URI del broker
        parsed_uri = urllib.parse.urlparse(broker_uri)
        broker_host = parsed_uri.hostname or '127.0.0.1'
        broker_port = parsed_uri.port or 1883

        self.stdout.write(self.style.NOTICE(f"Inicializando MQTT Listener en {broker_host}:{broker_port}..."))

        client = mqtt.Client(client_id="django_backend_listener", clean_session=False)
        
        # Inyectar credenciales Zero-Trust
        client.username_pw_set(username="django_backend", password=hardware_key)
        
        # Asignar callbacks
        client.on_connect = self.on_connect
        client.on_message = self.on_message

        try:
            client.connect(broker_host, broker_port, 60)
            self.stdout.write(self.style.SUCCESS("Iniciando bucle bloqueante de consumo (loop_forever)..."))
            client.loop_forever()
        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING("\nApagando MQTT Listener de forma segura."))
            client.disconnect()
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error fatal en el cliente MQTT: {str(e)}"))
