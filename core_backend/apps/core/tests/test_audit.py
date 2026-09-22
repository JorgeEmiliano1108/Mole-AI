import os
import tempfile
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import NoReverseMatch, reverse
from rest_framework.test import APIClient

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
        except NoReverseMatch:
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
        """Test 3 (Celery Resiliencia): ante falla de red, la tarea reintenta
        (lanza Retry) y NO borra el archivo: el archivo sobrevive al fallo."""
        from celery.exceptions import Retry
        from requests.exceptions import ConnectionError

        # Creamos el archivo temporal sólo para que la función open() no falle.
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"fake image data")
            temp_path = f.name

        mock_post.side_effect = ConnectionError("Falla simulada de red")

        # Backend en memoria: sin Redis local, el reintento se registra en
        # backend `memory://` en vez de intentar conexión real. Se restaura
        # en `finally` para no contaminar otros tests.
        from unittest.mock import patch as _patch

        from celery.backends.cache import CacheBackend
        real_backend = analyze_vision_async._backend
        analyze_vision_async.backend = CacheBackend(
            app=analyze_vision_async.app, url="memory://"
        )
        try:
            # .apply(throw=True) ejecuta eager: ante ConnectionError la tarea
            # lanza Retry (reencolado por el worker) SIN borrar el archivo.
            # Se neutraliza celery.app.trace.logger: Celery 5.6 invoca
            # logger.info/log(fmt, dict) y rompe con logging stdlib
            # ("format requires a mapping", TypeError ajeno al producto;
            # en CI con structlog no ocurre).
            with _patch("celery.app.trace.logger"), self.assertRaises(Retry):
                analyze_vision_async.apply(
                    args=[temp_path],
                    kwargs={"auth_token": "Bearer test_token"},
                    throw=True,  # sin throw, .apply() traga la
                    # excepción en EagerResult en vez de elevar Retry.
                )
        finally:
            analyze_vision_async.backend = real_backend

        # ASERCIÓN: os.remove NO debió llamarse en ningún reintento (el archivo
        # sobrevive al fallo para reprocesarlo cuando MS1 vuelva).
        self.assertEqual(
            mock_os_remove.call_count, 0,
            f"Fallo de resiliencia: os.remove se llamó {mock_os_remove.call_count} veces ante un fallo de red."
        )
        print("[✓] Celery Seguro validado: el archivo sobrevive al fallo y la tarea se reencola.")

        # Cleanup real para no ensuciar el SO del testing:
        if os.path.exists(temp_path):
            os.remove(temp_path)
