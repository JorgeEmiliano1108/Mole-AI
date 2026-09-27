from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from apps.core.models import Device
from apps.core.tasks import check_device_liveness


class LivenessTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username='liv', password='x')

    def _dev(self, name, minutes_ago, interval=5, status='online'):
        from datetime import timedelta
        return Device.objects.create(
            owner=self.user, name=name, auth_token=f'tok-{name}',
            status=status, report_interval_minutes=interval,
            last_seen=(timezone.now() - timedelta(minutes=minutes_ago)
                       if minutes_ago is not None else None))

    def test_fresh_device_stays_online(self):
        self._dev('ok', minutes_ago=1)
        out = check_device_liveness()
        self.assertEqual(out, {"offline_count": 0, "warning_count": 0})
        self.assertEqual(Device.objects.get(name='ok').status, 'online')

    def test_missed_cycles_escalate(self):
        self._dev('warn', minutes_ago=11)   # >2x5, <4x5
        self._dev('off', minutes_ago=25)    # >4x5
        out = check_device_liveness()
        self.assertEqual(out['warning_count'], 1)
        self.assertEqual(out['offline_count'], 1)
        self.assertEqual(Device.objects.get(name='warn').status, 'warning')
        self.assertEqual(Device.objects.get(name='off').status, 'offline')

    def test_never_seen_skipped(self):
        self._dev('new', minutes_ago=None)
        out = check_device_liveness()
        self.assertEqual(out, {"offline_count": 0, "warning_count": 0})
