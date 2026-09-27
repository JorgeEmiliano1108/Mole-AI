from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from apps.core.models import Device, HardwareBinding
from apps.plants.models import UserPlant


class BindingsRbacTests(APITestCase):
    def setUp(self):
        User = get_user_model()
        self.owner = User.objects.create_user(username='bo', password='x')
        self.staff = User.objects.create_user(username='bs', password='x',
                                              is_staff=True)
        self.plant = UserPlant.objects.create(user=self.owner, nickname='P')
        self.dev = Device.objects.create(owner=self.owner, name='d',
                                         auth_token='tok-bb')

    def test_health_404_unknown(self):
        self.client.force_authenticate(user=self.owner)
        resp = self.client.get('/api/v1/devices/00000000-0000-0000-0000-000000000000/health/')
        self.assertEqual(resp.status_code, 404)

    def test_bindings_post_staff_only(self):
        url = f'/api/v1/devices/{self.dev.id}/bindings/'
        self.client.force_authenticate(user=self.owner)
        resp = self.client.post(url, {'hardware_pin': '33',
                                      'plant_id': str(self.plant.id)},
                                format='json')
        self.assertEqual(resp.status_code, 403)

        self.client.force_authenticate(user=self.staff)
        resp = self.client.post(url, {'hardware_pin': '33',
                                      'plant_id': str(self.plant.id)},
                                format='json')
        self.assertEqual(resp.status_code, 201)
        self.assertTrue(HardwareBinding.objects.filter(
            device=self.dev, hardware_pin='33').exists())

    def test_bindings_post_validation(self):
        self.client.force_authenticate(user=self.staff)
        url = f'/api/v1/devices/{self.dev.id}/bindings/'
        resp = self.client.post(url, {}, format='json')
        self.assertEqual(resp.status_code, 400)
        resp = self.client.post(
            url, {'hardware_pin': '33', 'plant_id': str(self.plant.id)},
            format='json')
        self.assertEqual(resp.status_code, 201)
        resp = self.client.post(
            url, {'hardware_pin': '33', 'plant_id': str(self.plant.id)},
            format='json')
        self.assertEqual(resp.status_code, 409)

    def test_bindings_delete_staff_only(self):
        b = HardwareBinding.objects.create(device=self.dev, hardware_pin='32',
                                           plant=self.plant)
        url = f'/api/v1/devices/{self.dev.id}/bindings/{b.pk}/'
        self.client.force_authenticate(user=self.owner)
        self.assertEqual(self.client.delete(url).status_code, 403)
        self.client.force_authenticate(user=self.staff)
        self.assertEqual(self.client.delete(url).status_code, 204)
        self.assertFalse(HardwareBinding.objects.filter(pk=b.pk).exists())
