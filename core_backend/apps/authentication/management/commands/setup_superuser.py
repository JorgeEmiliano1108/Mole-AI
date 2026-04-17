import os
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

class Command(BaseCommand):
    help = 'Asegura la existencia del superusuario EmiMole con todos los permisos activos.'

    def handle(self, *args, **options):
        User = get_user_model()
        username = 'EmiMole'
        email = 'emi@mole.ai'
        password = 'moleai2026'

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
