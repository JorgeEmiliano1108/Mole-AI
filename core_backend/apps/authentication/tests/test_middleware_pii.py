import logging

from django.test import RequestFactory, TestCase

from apps.authentication.infrastructure.logging_filters import (
    PIIFilter,
    get_anonymized_email,
    get_hashed_user_id,
)
from apps.authentication.middleware import JwtHttpMiddleware


class PiiFilterTests(TestCase):
    def test_mask_email(self):
        self.assertEqual(get_anonymized_email('jorge@finca.com'), 'j***e@finca.com')
        self.assertEqual(get_anonymized_email('no-es-email'), 'no-es-email')

    def test_hash_stable_and_truncated(self):
        h1 = get_hashed_user_id('42')
        h2 = get_hashed_user_id('42')
        self.assertEqual(h1, h2)
        self.assertNotIn('42', h1)

    def test_filter_sanitizes_record(self):
        f = PIIFilter()
        rec = logging.LogRecord('x', logging.INFO, __file__, 1,
                                'login %s ok', ('jorge@finca.com',), None)
        self.assertTrue(f.filter(rec))
        self.assertNotIn('jorge@finca.com', rec.getMessage())
        self.assertIn('j***e@finca.com', rec.getMessage())


class JwtMiddlewareTests(TestCase):
    def test_passthrough_non_iot(self):
        mw = JwtHttpMiddleware(lambda req: 'OK')
        req = RequestFactory().get('/api/v1/plants/search/')
        self.assertEqual(mw(req), 'OK')

    def test_passthrough_get_on_protected(self):
        mw = JwtHttpMiddleware(lambda req: 'OK')
        req = RequestFactory().get('/api/v1/sensor-data/edge-batch/')
        self.assertEqual(mw(req), 'OK')

    def test_post_without_token_falls_through_to_legacy(self):
        # Sin Bearer pasa al flujo legacy HardwareAPIKey (vista lo valida).
        mw = JwtHttpMiddleware(lambda req: 'OK')
        req = RequestFactory().post('/api/v1/sensor-data/edge-batch/', {})
        self.assertEqual(mw(req), 'OK')

    def test_malformed_jwt_rejected(self):
        mw = JwtHttpMiddleware(lambda req: 'OK')
        req = RequestFactory().post(
            '/api/v1/sensor-data/edge-batch/', {},
            HTTP_AUTHORIZATION='Bearer a.b.c')
        resp = mw(req)
        self.assertIn(resp.status_code, (401, 403))
