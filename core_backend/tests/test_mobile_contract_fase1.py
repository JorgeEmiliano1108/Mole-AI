"""Contrato móvil Fase 1 (issue 11): paginación, health público, orden favorites/.

Estos tests fijan decisiones del contrato que el APK Flutter asume:
- GET /api/v1/health/ es público (ping pre-login).
- GET /api/v1/plants/species/ responde envelope paginado {count, results}.
- /api/v1/user-plants/favorites/ resuelve a favoritos, no a detail por UUID.
"""
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase


class MobileContractFase1Tests(APITestCase):
    def test_health_public_sin_jwt(self):
        resp = self.client.get("/api/v1/health/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json().get("status"), "healthy")

    def test_species_list_paginada(self):
        resp = self.client.get("/api/v1/plants/species/")
        # Lectura pública (IsSuperuserOrReadOnly) + envelope paginado PAGE_SIZE=50.
        self.assertEqual(resp.status_code, 200)
        payload = resp.json()
        self.assertIn("count", payload)
        self.assertIn("results", payload)
        self.assertIsInstance(payload["results"], list)

    def test_favorites_no_colisiona_con_uuid(self):
        user = get_user_model().objects.create_user(username="movil_f1", password="x")
        self.client.force_authenticate(user=user)
        resp = self.client.get("/api/v1/user-plants/favorites/")
        # 200 envelope (o 404 si el orden fuera erróneo); nunca 404 por UUID.
        self.assertEqual(resp.status_code, 200)
        self.assertIn("results", resp.json())
