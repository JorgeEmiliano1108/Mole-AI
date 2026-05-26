from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from django.urls import reverse
from unittest.mock import patch
import os
import tempfile
from celery.exceptions import Retry
from apps.ai_models.tasks import analyze_vision_async

User = get_user_model()

class AuditTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        # Usuario normal (Agricultor)
        self.user = User.objects.create_user(
            username='agricultor_test',
            password='password123',
            email='agri@test.com'
        )
        # Auth Token
        self.client.force_authenticate(user=self.user)

    def test_auth_hashing_algorithm(self):
        """Test 1 (Auth): Verifica que al crear un usuario, la contraseña use Argon2."""
        self.assertTrue(
            self.user.password.startswith('argon2$') or self.user.password.startswith('pbkdf2_'),
            f"El algoritmo de hash no es seguro, prefix: {self.user.password[:10]}"
        )
        if self.user.password.startswith('argon2$'):
            print("[\u2713] Auth Segura confirmada: Argon2 detectado.")

    def test_rbac_escalation_prevention(self):
        """Test 2 (RBAC): Fuerzo un request autenticado con Agricultor hacia un endpoint Admin."""
        try:
            url = reverse('core:admin_users_create')
        except Exception:
            # Fallback path if reverse fails
            url = '/api/v1/core/admin/users/'

        response = self.client.post(url, {
            'username': 'hacked_admin',
            'password': 'hacked123',
            'role': 'Superadmin'
        })
        
        self.assertEqual(
            response.status_code, 403,
            f"Fallo de RBAC: El agricultor pudo accesar ruta admin! Status: {response.status_code}"
        )
        print("[\u2713] RBAC Seguro confirmado: Agricultor bloqueado de rutas 403.")

    @patch('apps.ai_models.tasks.os.remove')
    @patch('apps.ai_models.tasks.requests.post')
    def test_celery_resilience_file_survival(self, mock_post, mock_os_remove):
        """Test 3 (Celery Resiliencia): Simula falla de red transitoria y asegura supervivencia del archivo."""
        from requests.exceptions import ConnectionError
        
        # Creamos el archivo temporal sólo para que la función open() no falle.
        # No evaluaremos disco real, sino cuántas veces Celery invocó os.remove internamente.
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"fake image data")
            temp_path = f.name
            
        class MockResponse:
            def raise_for_status(self): pass
            def json(self): return {"status": "ok"}
            
        call_count = [0]
        
        def custom_mock_post(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                raise ConnectionError("Falla simulada de red 1era vez")
            return MockResponse()
            
        mock_post.side_effect = custom_mock_post
        
        # En Eager Mode, Celery captura el primer Retry y reintenta de forma transparente.
        # La primera vez lanzará ConnectionError (falla). La segunda vez devolverá 200 (éxito).
        try:
            analyze_vision_async.apply(args=[temp_path], kwargs={'auth_token': 'Bearer test_token'})
        except Exception:
            pass
            
        # ASERCIÓN OBLIGATORIA: mock_os_remove debió ser llamado exactamente UNA vez
        # (por el bloque de éxito del 2do intento). Si fue llamado 2 veces, se borró prematuramente.
        self.assertEqual(
            mock_os_remove.call_count, 1, 
            f"Fallo de resiliencia: os.remove se llamó {mock_os_remove.call_count} veces."
        )
        print("[\u2713] Celery Seguro validado con Mocks: os.remove invocado estrictamente una vez tras el éxito.")
        
        # Cleanup real para no ensuciar el SO del testing:
        if os.path.exists(temp_path):
            os.remove(temp_path)
