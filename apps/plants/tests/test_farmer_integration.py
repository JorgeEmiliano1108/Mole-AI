from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from apps.plants.infrastructure.repositories.models import UserPlant
from apps.core.infrastructure.repositories.models import SensorLog


class FarmerIntegrationTests(APITestCase):
    """Integration tests for farmer dashboard endpoints.

    Covers:
    - unauthenticated access rejection
    - user isolation for my-collection
    - telemetry latest returns injected telemetry for owned plant
    """

    def test_my_collection_requires_authentication(self):
        resp = self.client.get('/api/v1/plants/my-collection/')
        self.assertIn(resp.status_code, (401, 403))

    def test_my_collection_is_isolated_between_users(self):
        User = get_user_model()
        user_a = User.objects.create_user(username='farmer_a', password='password')
        user_b = User.objects.create_user(username='farmer_b', password='password')

        plant_a1 = UserPlant.objects.create(user=user_a, nickname='A1')
        plant_a2 = UserPlant.objects.create(user=user_a, nickname='A2')
        plant_b1 = UserPlant.objects.create(user=user_b, nickname='B1')

        # Authenticate as user_a
        self.client.force_authenticate(user=user_a)
        resp = self.client.get('/api/v1/plants/my-collection/')
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIsInstance(data, list)
        returned_ids = {item.get('id') for item in data}
        self.assertIn(str(plant_a1.id), returned_ids)
        self.assertIn(str(plant_a2.id), returned_ids)
        self.assertNotIn(str(plant_b1.id), returned_ids)

    def test_telemetry_latest_returns_injected_values(self):
        User = get_user_model()
        user = User.objects.create_user(username='farmer_c', password='password')
        plant = UserPlant.objects.create(user=user, nickname='C1')

        # Inject a sensor log for this plant
        log = SensorLog.objects.create(
            plant_id=plant.id,
            soil_humidity=42.5,
            air_humidity=50.0,
            air_temperature=23.7,
            uv_index=2.0,
            ph_level=6.4,
        )

        self.client.force_authenticate(user=user)
        resp = self.client.get(f'/api/v1/telemetry/latest/?plant_id={plant.id}')
        self.assertEqual(resp.status_code, 200)
        payload = resp.json()

        # The view returns the exact fields we inserted
        self.assertAlmostEqual(float(payload.get('soil_humidity')), 42.5)
        self.assertAlmostEqual(float(payload.get('air_temperature')), 23.7)
        self.assertAlmostEqual(float(payload.get('uv_index')), 2.0)
        self.assertAlmostEqual(float(payload.get('ph_level')), 6.4)
