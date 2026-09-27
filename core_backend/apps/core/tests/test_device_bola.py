from apps.core.models import Device, HardwareBinding
from apps.plants.models import UserPlant
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase


class DeviceBolaTests(APITestCase):
    """BOLA devices/health+bindings: solo dueño o staff (issue S2)."""

    def setUp(self):
        User = get_user_model()
        self.owner = User.objects.create_user(username='own', password='x')
        self.outsider = User.objects.create_user(username='out', password='x')
        self.staff = User.objects.create_user(
            username='stf', password='x', is_staff=True)
        plant = UserPlant.objects.create(user=self.owner, nickname='P')
        self.dev = Device.objects.create(
            owner=self.owner, name='nodo', auth_token='tok-bola', status='online')
        HardwareBinding.objects.create(
            device=self.dev, hardware_pin='32', plant=plant)
        self.url = f'/api/v1/devices/{self.dev.id}/health/'
        self.bind_url = f'/api/v1/devices/{self.dev.id}/bindings/'

    def test_owner_sees_own_device(self):
        self.client.force_authenticate(user=self.owner)
        self.assertEqual(self.client.get(self.url).status_code, 200)
        self.assertEqual(self.client.get(self.bind_url).status_code, 200)

    def test_outsider_gets_404_no_oracle(self):
        self.client.force_authenticate(user=self.outsider)
        self.assertEqual(self.client.get(self.url).status_code, 404)
        self.assertEqual(self.client.get(self.bind_url).status_code, 404)

    def test_staff_sees_any_device(self):
        self.client.force_authenticate(user=self.staff)
        self.assertEqual(self.client.get(self.url).status_code, 200)

    def test_anonymous_rejected(self):
        self.assertIn(self.client.get(self.url).status_code, (401, 403))
