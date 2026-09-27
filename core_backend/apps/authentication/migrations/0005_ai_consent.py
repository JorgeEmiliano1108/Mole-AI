from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0004_add_password_reset_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='ai_consent',
            field=models.BooleanField(default=False, help_text='Consentimiento separado para inferencia IA (diagnóstico por foto, chat RAG). Sin esto, los endpoints IA responden 403.'),
        ),
        migrations.AddField(
            model_name='user',
            name='ai_consent_date',
            field=models.DateTimeField(blank=True, help_text='Fecha y hora en que se otorgó el consentimiento de IA.', null=True),
        ),
    ]
