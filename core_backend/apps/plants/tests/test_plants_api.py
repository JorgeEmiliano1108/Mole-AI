from apps.plants.models import FavoritePlant, UserPlant
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase


class PlantsApiTests(APITestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username='pl', password='x')
        self.admin = User.objects.create_user(username='pla', password='x',
                                              is_staff=True)
        self.client.force_authenticate(user=self.user)

    def test_favorites_flow(self):
        p = UserPlant.objects.create(user=self.user, nickname='F')
        resp = self.client.post('/api/v1/user-plants/favorites/',
                                {'plant': str(p.id)}, format='json')
        self.assertEqual(resp.status_code, 201)
        resp = self.client.get('/api/v1/user-plants/favorites/')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()['count'], 1)

    def test_flora_create_requires_auth(self):
        resp = self.client.post('/api/v1/plants/flora/', {}, format='json')
        # Autenticado: pasa auth (puede fallar por validación, no por permiso).
        self.assertNotIn(resp.status_code, (401, 403))

    def test_plant_detail_isolated(self):
        User = get_user_model()
        otro = User.objects.create_user(username='plo', password='x')
        ajena = UserPlant.objects.create(user=otro, nickname='X')
        resp = self.client.get(f'/api/v1/user-plants/{ajena.id}/')
        self.assertEqual(resp.status_code, 404)

    def test_favorite_delete_scoped(self):
        User = get_user_model()
        otro = User.objects.create_user(username='plo2', password='x')
        ajena = FavoritePlant.objects.create(
            plant=UserPlant.objects.create(user=otro, nickname='Y'),
            user=otro)
        # Borrar favorito ajeno: 404 (scoped por usuario).
        resp = self.client.delete(f'/api/v1/user-plants/favorites/{ajena.id}/')
        self.assertEqual(resp.status_code, 404)
        self.assertTrue(FavoritePlant.objects.filter(id=ajena.id).exists())
