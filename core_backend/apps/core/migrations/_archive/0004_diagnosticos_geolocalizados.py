# Generated migration for DiagnosticoGeolocalizado model
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):

    dependencies = [
        ('core', '0003_wide_table_sensor_logs'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='DiagnosticoGeolocalizado',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('condition_name', models.CharField(blank=True, max_length=200)),
                ('latitude', models.FloatField(blank=True, null=True, db_index=True)),
                ('longitude', models.FloatField(blank=True, null=True, db_index=True)),
                ('severity', models.CharField(choices=[('low', 'Low'), ('medium', 'Medium'), ('high', 'High'), ('critical', 'Critical')], default='medium', max_length=10)),
                ('metadata', models.JSONField(blank=True, default=dict)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('diagnostic', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='geolocations', to='core.aidiagnostic')),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'diagnosticos_geolocalizados',
            },
        ),
    ]
