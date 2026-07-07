"""Migration to add owner FK to Device model."""

from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('core', '0009_add_is_active'),
    ]

    operations = [
        migrations.AddField(
            model_name='device',
            name='owner',
            field=models.ForeignKey(on_delete=models.CASCADE, related_name='devices', to='auth.User'),
        ),
    ]
