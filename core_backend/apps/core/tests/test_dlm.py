from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from apps.core.models import (
    Device,
    HardwareBinding,
    HourlySoilAggregate,
    SoilReading,
)
from apps.core.tasks import downsample_telemetry, purge_raw_telemetry
from apps.plants.models import UserPlant


class DlmTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username='dlm', password='x')
        plant = UserPlant.objects.create(user=self.user, nickname='D')
        self.dev = Device.objects.create(owner=self.user, name='d',
                                         auth_token='tok-dlm')
        self.bind = HardwareBinding.objects.create(
            device=self.dev, hardware_pin='32', plant=plant)

    def _old_reading(self, **kw):
        from datetime import timedelta
        old = timezone.now() - timedelta(days=40)
        kw.setdefault('recorded_at', old)
        return SoilReading.objects.create(binding=self.bind, **kw)

    def test_downsample_creates_aggregates(self):
        self._old_reading(soil_humidity=30.0)
        self._old_reading(soil_humidity=50.0)
        out = downsample_telemetry()
        aggs = HourlySoilAggregate.objects.filter(binding=self.bind)
        self.assertGreaterEqual(aggs.count(), 1)
        self.assertAlmostEqual(aggs.first().avg_soil_humidity, 40.0)
        self.assertIn('soil', str(out).lower() + 'aggregates')

    def test_purge_requires_archive(self):
        # Sin archive verificado: fail-safe, no borra nada.
        self._old_reading(soil_humidity=30.0)
        out = purge_raw_telemetry()
        self.assertEqual(out, {"soil_purged": 0, "ambient_purged": 0})
        self.assertEqual(SoilReading.objects.count(), 1)

    def test_purge_with_archive_deletes(self):
        from datetime import timedelta

        from apps.core.models import TelemetryArchive
        self._old_reading(soil_humidity=30.0)
        cutoff = timezone.now() - timedelta(days=30)
        period = cutoff.strftime('%Y-%m')
        TelemetryArchive.objects.create(
            device=self.dev, period_start=cutoff,
            period_end=timezone.now(), rows_archived=1,
            s3_key=f"telemetry-archive/{self.dev.pk}/{period}_soil.csv.gz")
        out = purge_raw_telemetry()
        self.assertEqual(out["soil_purged"], 1)
        self.assertEqual(SoilReading.objects.count(), 0)
