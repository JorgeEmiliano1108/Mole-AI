from apps.core.models import AmbientReading, Device, HardwareBinding, SoilReading
from apps.plants.models import UserPlant
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase


def _device(owner, name, status="online", token="tok"):
    return Device.objects.create(owner=owner, name=name, auth_token=f"{token}-{name}",
                                 status=status)


class MyAlertsTests(APITestCase):
    """GET /api/v1/user-plants/my-alerts/ — scoped por propiedad (issue N-0)."""

    def test_my_alerts_requires_authentication(self):
        resp = self.client.get('/api/v1/user-plants/my-alerts/')
        self.assertIn(resp.status_code, (401, 403))

    def test_my_alerts_scoped_to_owner(self):
        User = get_user_model()
        ana = User.objects.create_user(username='ana', password='x')
        beto = User.objects.create_user(username='beto', password='x')

        pa = UserPlant.objects.create(user=ana, nickname='PA')
        pb = UserPlant.objects.create(user=beto, nickname='PB')
        da = _device(ana, 'nodo-ana')
        db = _device(beto, 'nodo-beto')
        ba = HardwareBinding.objects.create(device=da, hardware_pin='32', plant=pa)
        bb = HardwareBinding.objects.create(device=db, hardware_pin='32', plant=pb)
        SoilReading.objects.create(binding=ba, soil_humidity=10.0)
        SoilReading.objects.create(binding=bb, soil_humidity=10.0)
        AmbientReading.objects.create(device=db, uv_index=12.0)

        self.client.force_authenticate(user=ana)
        resp = self.client.get('/api/v1/user-plants/my-alerts/')
        self.assertEqual(resp.status_code, 200)
        alerts = resp.json()['alerts']
        # Solo la humedad crítica propia; ni la de beto ni su UV.
        self.assertEqual(len(alerts), 1)
        self.assertEqual(alerts[0]['tipo'], 'error')
        self.assertEqual(alerts[0]['plant_id'], str(pa.id))

    def test_my_alerts_liveness_owned_device(self):
        User = get_user_model()
        ana = User.objects.create_user(username='ana2', password='x')
        _device(ana, 'nodo-caido', status='offline')

        self.client.force_authenticate(user=ana)
        resp = self.client.get('/api/v1/user-plants/my-alerts/')
        self.assertEqual(resp.status_code, 200)
        alerts = resp.json()['alerts']
        live = [a for a in alerts if a.get('source') == 'liveness']
        self.assertEqual(len(live), 1)
        self.assertEqual(live[0]['tipo'], 'error')

    def test_my_alerts_stable_when_empty(self):
        User = get_user_model()
        ana = User.objects.create_user(username='ana3', password='x')

        self.client.force_authenticate(user=ana)
        resp = self.client.get('/api/v1/user-plants/my-alerts/')
        self.assertEqual(resp.status_code, 200)
        alerts = resp.json()['alerts']
        self.assertEqual(len(alerts), 1)
        self.assertEqual(alerts[0]['tipo'], 'info')
