from unittest.mock import MagicMock, patch

from django.test import TestCase


class WeatherProxyTests(TestCase):
    def test_tile_no_key_501(self):
        with patch.dict('os.environ', {}, clear=False):
            import os
            os.environ.pop('OPENWEATHER_API_KEY', None)
            resp = self.client.get('/api/v1/weather/tile/temp/1/2/3.png')
            self.assertEqual(resp.status_code, 501)

    def test_tile_proxies_png(self):
        raw = MagicMock()
        r = MagicMock(status_code=200, raw=raw)
        with (patch.dict('os.environ', {'OPENWEATHER_API_KEY': 'k'}),
              patch('apps.core.views.requests.get', return_value=r)):
            resp = self.client.get('/api/v1/weather/tile/temp/1/2/3.png')
        self.assertEqual(resp.status_code, 200)

    def test_current_requires_coords(self):
        resp = self.client.get('/api/v1/weather/current/')
        self.assertEqual(resp.status_code, 400)

    def test_current_no_key_501(self):
        import os
        os.environ.pop('OPENWEATHER_API_KEY', None)
        resp = self.client.get('/api/v1/weather/current/?lat=19&lon=-99')
        self.assertEqual(resp.status_code, 501)

    def test_current_proxies_json(self):
        fake = MagicMock(status_code=200)
        fake.json.return_value = {'main': {'temp': 22.0}}
        with (patch.dict('os.environ', {'OPENWEATHER_API_KEY': 'k'}),
              patch('apps.core.views.requests.get', return_value=fake)):
            resp = self.client.get('/api/v1/weather/current/?lat=19&lon=-99')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()['main']['temp'], 22.0)
