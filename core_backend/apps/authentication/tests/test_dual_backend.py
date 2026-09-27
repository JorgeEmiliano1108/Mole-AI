from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.authentication.backends import DualLoginBackend


class DualLoginTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(
            username='juan', email='Juan@X.io', password='secretas')
        self.be = DualLoginBackend()

    def test_login_username(self):
        self.assertEqual(
            self.be.authenticate(None, username='juan', password='secretas'),
            self.user)

    def test_login_email_case_insensitive(self):
        self.assertEqual(
            self.be.authenticate(None, username='JUAN@x.IO', password='secretas'),
            self.user)

    def test_wrong_password_none(self):
        self.assertIsNone(
            self.be.authenticate(None, username='juan', password='mala'))

    def test_unknown_user_none(self):
        self.assertIsNone(
            self.be.authenticate(None, username='nadie', password='x'))

    def test_missing_args_none(self):
        self.assertIsNone(self.be.authenticate(None))
        self.assertIsNone(
            self.be.authenticate(None, username='juan', password=None))

    def test_inactive_blocked(self):
        self.user.is_active = False
        self.user.save()
        self.assertIsNone(
            self.be.authenticate(None, username='juan', password='secretas'))
        self.assertFalse(self.be.user_can_authenticate(self.user))
