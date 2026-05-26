# =============================================================================
# Copyright (C) 2024-2026 Mole.AI — All Rights Reserved.
# =============================================================================
"""
Tests para cumplimiento NOM-059 (protección de flora mexicana).
Valida que las especies protegidas incluyan advertencia legal en búsqueda.
"""
from django.test import TestCase, Client
from rest_framework import status
from apps.plants.models import SpeciesCatalog


class NOM059ComplianceTestCase(TestCase):
    """Test cases para NOM-059-SEMARNAT-2010 (Protección de Flora Silvestre)."""

    def setUp(self):
        self.client = Client()
        self.protected_species = SpeciesCatalog.objects.create(
            scientific_name="Pseudotsuga menziesii",
            common_name="Oyamel",
            is_protected_nom059=True,
            protection_category="P",
            description="Especie de conífera protegida en México."
        )
        self.threatened_species = SpeciesCatalog.objects.create(
            scientific_name="Seemannia sylvatica",
            common_name="Gloxinia silvestre",
            is_protected_nom059=True,
            protection_category="T",
            description="Especie amenazada."
        )
        self.unprotected_species = SpeciesCatalog.objects.create(
            scientific_name="Solanum lycopersicum",
            common_name="Tomate",
            is_protected_nom059=False,
            description="Cultivo común no protegido."
        )

    def test_protected_species_includes_warning(self):
        """Verificar que especie protegida incluye flag y advertencia legal."""
        response = self.client.get("/api/v1/plants/search/?q=Oyamel")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()

        self.assertTrue(data.get("is_protected_nom059"))
        self.assertIn("protection_warning", data)
        self.assertIn("NOM-059", data["protection_warning"])
        self.assertEqual(data.get("protection_category"), "P")

    def test_threatened_species_includes_warning(self):
        """Verificar que especie amenazada incluye advertencia."""
        response = self.client.get("/api/v1/plants/search/?q=Gloxinia")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()

        self.assertTrue(data.get("is_protected_nom059"))
        self.assertIn("protection_warning", data)
        self.assertEqual(data.get("protection_category"), "T")

    def test_unprotected_species_no_warning(self):
        """Verificar que especie no protegida NO incluye advertencia."""
        response = self.client.get("/api/v1/plants/search/?q=Tomate")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()

        self.assertFalse(data.get("is_protected_nom059", False))
        self.assertNotIn("protection_warning", data)
        self.assertNotIn("protection_category", data)

    def test_search_by_scientific_name(self):
        """Verificar búsqueda también incluye advertencia."""
        response = self.client.get("/api/v1/plants/search/?q=Pseudotsuga")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertTrue(data.get("is_protected_nom059"))

    def test_not_found_species(self):
        """Verificar que especie no encontrada devuelve 404."""
        response = self.client.get("/api/v1/plants/search/?q=EspecieInexistente")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_missing_query_parameter(self):
        """Verificar que query sin parámetro q devuelve 400."""
        response = self.client.get("/api/v1/plants/search/")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)