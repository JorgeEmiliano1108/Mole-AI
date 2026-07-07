"""Migration to add soft‑delete flag is_active to Device model."""

from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('core', '0008_device_last_seen_alter_device_status'),  # previous migration name, adjust if needed
    ]

    operations = [
        migrations.AddField(
            model_name='device',
            name='is_active',
            field=models.BooleanField(default=True, help_text='Soft‑delete flag'),
        ),
    ]
