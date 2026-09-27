from django.test import TestCase
from rest_framework import serializers

from apps.authentication.tasks import (
    generate_email_token,
    generate_password_reset_token,
)
from apps.authentication.token_denylist import deny_jti, is_denied
from apps.authentication.validators import (
    SecurePasswordValidator,
    validate_password_strength,
)


class AuthUtilsTests(TestCase):
    def test_tokens_unique_and_shaped(self):
        t1 = generate_email_token(7)
        t2 = generate_email_token(7)
        self.assertEqual(len(t1), 64)
        self.assertNotEqual(t1, t2)
        self.assertEqual(len(generate_password_reset_token(9)), 64)

    def test_password_strength(self):
        ok, _ = validate_password_strength('Segura123')
        self.assertTrue(ok)
        ok, msg = validate_password_strength('corta')
        self.assertFalse(ok)
        self.assertIn('6 caracteres', msg)
        with self.assertRaises(serializers.ValidationError):
            SecurePasswordValidator().validate('abc')
        self.assertEqual(
            SecurePasswordValidator().validate('Segura123'), 'Segura123')

    def test_denylist_roundtrip(self):
        self.assertFalse(is_denied(None))
        self.assertFalse(is_denied('nope'))
        deny_jti(None, 60)
        deny_jti('jti-1', 60)
        self.assertTrue(is_denied('jti-1'))
