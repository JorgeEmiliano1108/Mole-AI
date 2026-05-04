"""
Mole.AI - Sprint 1: CSRF Protection Patch
Objetivo: Verificar que CSRF_TRUSTED_ORIGINS valida correctamente los orígenes.
Metodología: TDD Red-Green-Refactor
"""

import pytest
from django.test import TestCase
from django.conf import settings


class TestCsrfTrustedOrigins(TestCase):
    """
    Fase RED: Tests que deben FALLAR porque CSRF_TRUSTED_ORIGINS 
    aún no está configurado correctamente para producción.
    """
    
    def test_trusted_origins_for_development(self):
        """
        Test: En modo DEBUG=True, localhost debe estar en CSRF_TRUSTED_ORIGINS.
        Fase GREEN: Debe PASAR porque .env tiene CSRF_TRUSTED_ORIGINS configurado.
        """
        trusted = settings.CSRF_TRUSTED_ORIGINS
        # En desarrollo, localhost debe ser confiable
        # Debug: print actual value for debugging
        print(f"\nDEBUG CSRF_TRUSTED_ORIGINS: {trusted}")
        has_localhost = any('localhost' in t for t in trusted)
        assert has_localhost, \
            f"ERROR: localhost no está en CSRF_TRUSTED_ORIGINS. Actual: {trusted}"
    
    def test_trusted_origins_rejects_untrusted(self):
        """
        Test: Orígenes no confiables deben ser rechazados.
        Fase RED: Este test debe PASAR (comportamiento esperado).
        """
        trusted = settings.CSRF_TRUSTED_ORIGINS
        # Orígenes maliciosos NO deben estar
        assert 'https://evil.com' not in trusted, \
            "ERROR: evil.com está en orígenes confiables"
        assert 'http://attacker.net' not in trusted, \
            "ERROR: attacker.net está en orígenes confiables"
    
    def test_trusted_origins_production_ready(self):
        """
        Test: CSRF_TRUSTED_ORIGINS debe tener orígenes reales para producción.
        Fase RED: Falla porque .env.example tiene valores vacíos o por defecto.
        """
        trusted = settings.CSRF_TRUSTED_ORIGINS
        # En producción debe haber orígenes reales (no solo localhost)
        production_origins = [o for o in trusted if 'localhost' not in o]
        
        # Fase RED: En .env.example está vacío → falla
        # Fase GREEN: Después de configurar → test PASARÁ
        assert len(production_origins) > 0, \
            f"ERROR: No hay orígenes de producción configurados. Actual: {trusted}"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
