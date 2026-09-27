from django.test import TestCase

from apps.authentication.jwks import fetch_jwks, get_verification_key
from apps.core.fields import EncryptedCharField


class FieldsTests(TestCase):
    def test_encrypted_roundtrip(self):
        f = EncryptedCharField(max_length=128)
        prep = f.get_prep_value('sekret-token')
        self.assertNotIn('sekret-token', str(prep))
        back = f.from_db_value(prep, None, None)
        self.assertEqual(back, 'sekret-token')

    def test_empty_passthrough(self):
        f = EncryptedCharField(max_length=128)
        self.assertIsNone(f.get_prep_value(None))
        self.assertIsNone(f.from_db_value(None, None, None))


class JwksTests(TestCase):
    def test_local_key(self):
        key, algs = get_verification_key('x.y.z')
        self.assertTrue(key)
        self.assertEqual(algs, ['HS256'])

    def test_fetch_noop(self):
        self.assertEqual(fetch_jwks(), {'keys': []})
