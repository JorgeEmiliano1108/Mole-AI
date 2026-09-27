import time

import httpx
from django.test import TestCase

from apps.core.infrastructure.clients.microservices import (
    BaseMicroserviceClient,
    MicroserviceClientFactory,
    ServiceConfig,
    ServiceResponse,
)


def _resp(status, payload):
    return httpx.Response(status, json=payload,
                          request=httpx.Request('GET', 'http://h'))


class _Concrete(BaseMicroserviceClient):
    async def _do(self):
        return None


class MicroserviceClientTests(TestCase):
    def test_config_defaults(self):
        c = ServiceConfig(name='x', base_url='http://h')
        self.assertEqual(c.timeout_seconds, 30)
        self.assertEqual(c.max_retries, 3)
        self.assertIsNone(c.api_key)

    def test_headers_with_and_without_key(self):
        plain = _Concrete(ServiceConfig(name='x', base_url='http://h'))
        self.assertNotIn('Authorization', plain._build_headers())
        keyed = _Concrete(ServiceConfig(name='x', base_url='http://h',
                                        api_key='k'))
        self.assertEqual(keyed._build_headers()['Authorization'], 'Bearer k')
        self.assertEqual(keyed._build_headers()['User-Agent'],
                         'Mole-AI-Backend/1.0')

    def test_handle_response_ok(self):
        resp = _resp(200, {'a': 1})
        out = BaseMicroserviceClient._handle_response(resp, time.time())
        self.assertTrue(out.success)
        self.assertEqual(out.data, {'a': 1})
        self.assertEqual(out.status_code, 200)
        self.assertIsInstance(out, ServiceResponse)

    def test_handle_response_error(self):
        resp = _resp(500, {'e': 1})
        out = BaseMicroserviceClient._handle_response(resp, time.time())
        self.assertFalse(out.success)
        self.assertEqual(out.status_code, 500)

    def test_factory_ai_client(self):
        c = MicroserviceClientFactory.create_ai_client()
        self.assertEqual(c.config.name, 'AI Service')
        self.assertEqual(c.config.timeout_seconds, 60)

    def test_factory_data_client(self):
        c = MicroserviceClientFactory.create_data_processing_client()
        self.assertEqual(c.config.name, 'Mole-AI Service')
