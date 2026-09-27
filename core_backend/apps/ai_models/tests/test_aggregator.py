from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.ai_models.services import MoleAIClient, SensorDataAggregator
from apps.core.models import SensorLog
from apps.plants.models import UserPlant


class AggregatorTests(TestCase):
    def test_empty_window_returns_empty(self):
        self.assertEqual(
            SensorDataAggregator.get_latest_sensor_readings(), {})

    def test_latest_reading_by_plant(self):
        User = get_user_model()
        u = User.objects.create_user(username='agg', password='x')
        p = UserPlant.objects.create(user=u, nickname='A')
        SensorLog.objects.create(plant_id=p.id, soil_humidity=30.0)
        SensorLog.objects.create(plant_id=p.id, soil_humidity=44.0)
        out = SensorDataAggregator.get_latest_sensor_readings(
            plant_id=str(p.id))
        self.assertEqual(out['soil_humidity'], 44.0)
        self.assertEqual(out['plant_id'], str(p.id))

    def test_client_config(self):
        c = MoleAIClient()
        self.assertTrue(c.base_url.startswith('http'))
        self.assertGreater(c.timeout, 0)
