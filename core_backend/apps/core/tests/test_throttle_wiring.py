from django.test import TestCase


class ThrottleWiringTests(TestCase):
    """Throttles declarados donde toca (issue S2). Sin red: verifica wiring."""

    def _throttles_of(self, view):
        return list(getattr(view, 'cls', view).throttle_classes
                    if hasattr(getattr(view, 'cls', view), 'throttle_classes')
                    else [])

    def test_auth_endpoints_have_anon_throttle(self):
        from apps.authentication import views as av
        from rest_framework.throttling import AnonRateThrottle
        for v in (av.login_view, av.register_view, av.password_reset_confirm_view):
            f = v.cls if hasattr(v, 'cls') else v
            self.assertIn(AnonRateThrottle, f.throttle_classes, v.__name__)

    def test_sensor_patch_has_throttle(self):
        from apps.core import views as cv
        f = cv.sensor_data_patch_view
        f = f.cls if hasattr(f, 'cls') else f
        self.assertTrue(len(f.throttle_classes) > 0)
