import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Asegura la existencia del superusuario EmiMole con todos los permisos activos.'

    def handle(self, *args, **options):
        User = get_user_model()
        username = 'EmiMole'
        email = 'emi@mole.ai'
        # V2 staging: sin default. Un password hardcodeado en repo es fuga
        # de credencial (ver issue 10/B7). Falla explícito si falta el env.
        password = os.getenv('DJANGO_SUPERUSER_PASSWORD', '')
        if not password:
            raise ValueError(
                "DJANGO_SUPERUSER_PASSWORD no definido: rehúso crear "
                "superusuario con credencial por defecto."
            )

        user, created = User.objects.get_or_create(
            username=username,
            defaults={'email': email}
        )
        
        if created:
            user.set_password(password)
            self.stdout.write(self.style.SUCCESS(f"Superusuario '{username}' creado exitosamente."))
        else:
            self.stdout.write(self.style.SUCCESS(f"Usuario '{username}' ya existía. Asegurando permisos..."))

        # Guarantee powers
        user.is_superuser = True
        user.is_staff = True
        user.is_active = True
        user.save()
        
        self.stdout.write(self.style.SUCCESS(f"El usuario '{username}' ahora es superadministrador total."))
