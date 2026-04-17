# Hand-written migration: add ph_level and air_humidity to SensorLog
# These fields align the Django model with the ESP32 hardware payload
# (air_humidity) and the CNN async-inference pipeline (ph_level).

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0005_botanicalknowledge_feedbackticket_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='sensorlog',
            name='ph_level',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='sensorlog',
            name='air_humidity',
            field=models.FloatField(blank=True, null=True),
        ),
    ]
