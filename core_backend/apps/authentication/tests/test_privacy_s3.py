from apps.core.models import AIDiagnostic, Device, SensorLog
from apps.plants.models import UserPlant
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase


class PrivacyS3Tests(APITestCase):
    """S3: consentimiento IA, export, olvido real, JWT mínimo (normativa)."""

    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username='s3u', password='x')

    def test_ai_consent_separado_del_general(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.post('/api/v1/auth/consent/', {'consent': True},
                                format='json')
        self.assertEqual(resp.status_code, 200)
        self.user.refresh_from_db()
        self.assertTrue(self.user.data_consent)
        self.assertFalse(self.user.ai_consent)

        resp = self.client.post('/api/v1/auth/consent/',
                                {'consent': True, 'ai_consent': True}, format='json')
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.json()['ai_consent'])
        self.user.refresh_from_db()
        self.assertTrue(self.user.ai_consent)
        self.assertIsNotNone(self.user.ai_consent_date)

    def test_ia_sin_consentimiento_403(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.post('/api/v1/llm/chat/', {'message': 'hola'},
                                format='json')
        self.assertEqual(resp.status_code, 403)
        self.assertEqual(resp.json().get('code'), 'CONSENT_REQUIRED')

    def test_jwt_minimo_sin_pii(self):
        import jwt as pyjwt
        from django.conf import settings
        resp = self.client.post('/api/v1/auth/login/',
                                {'username': 's3u', 'password': 'x'}, format='json')
        self.assertEqual(resp.status_code, 200)
        key = getattr(settings, 'JWT_SECRET_KEY', None) or settings.SECRET_KEY
        claims = pyjwt.decode(resp.json()['token'], key,
                              algorithms=['HS256'], audience='authenticated')
        self.assertIn('sub', claims)
        self.assertIn('role', claims)
        self.assertNotIn('username', claims)
        self.assertNotIn('email', claims)

    def test_export_contiene_solo_lo_propio(self):
        User = get_user_model()
        otro = User.objects.create_user(username='s3otro', password='x')
        UserPlant.objects.create(user=self.user, nickname='Mia')
        UserPlant.objects.create(user=otro, nickname='Ajena')

        self.client.force_authenticate(user=self.user)
        resp = self.client.get('/api/v1/auth/profile/export/')
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data['profile']['username'], 's3u')
        nicks = {p['nickname'] for p in data['plants']}
        self.assertIn('Mia', nicks)
        self.assertNotIn('Ajena', nicks)
        self.assertIn('ai_consent', data['profile'])

    def test_olvido_borra_en_cascada_y_conserva_auditoria(self):
        from apps.core.models import AuditLog
        plant = UserPlant.objects.create(user=self.user, nickname='Borrar')
        dev = Device.objects.create(owner=self.user, name='n',
                                    auth_token='tok-s3', status='online')
        SensorLog.objects.create(plant_id=plant.id, soil_humidity=50.0)
        AIDiagnostic.objects.create(user=self.user, plant_id=plant.id)

        self.client.force_authenticate(user=self.user)
        resp = self.client.delete('/api/v1/auth/profile/')
        self.assertEqual(resp.status_code, 204)

        self.assertFalse(UserPlant.objects.filter(id=plant.id).exists())
        self.assertFalse(Device.objects.filter(id=dev.id).exists())
        self.assertFalse(SensorLog.objects.filter(plant_id=plant.id).exists())
        self.assertFalse(AIDiagnostic.objects.filter(plant_id=plant.id).exists())
        self.assertTrue(AuditLog.objects.filter(
            action='DELETE_ACCOUNT_ARCO').exists())
