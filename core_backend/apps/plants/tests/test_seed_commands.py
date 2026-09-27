from apps.plants.models import SpeciesCatalog
from django.core.management import call_command
from django.test import TestCase


class SeedCommandsTests(TestCase):
    def test_seed_species_idempotent(self):
        call_command('seed_species')
        n1 = SpeciesCatalog.objects.count()
        self.assertGreater(n1, 0)
        call_command('seed_species')
        self.assertEqual(SpeciesCatalog.objects.count(), n1)
        self.assertTrue(SpeciesCatalog.objects.filter(
            scientific_name='Agave tequilana').exists())
