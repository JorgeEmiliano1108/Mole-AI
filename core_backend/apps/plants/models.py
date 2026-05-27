# =============================================================================
# Copyright (C) 2024-2026 Mole.AI — All Rights Reserved.
#
# AVISO DE PROPIEDAD INTELECTUAL:
# Este archivo es propiedad exclusiva de Mole.AI y sus autores originales.
# Queda estrictamente prohibida la copia, modificación, distribución,
# sublicenciamiento o uso comercial de este código, total o parcialmente,
# sin la autorización expresa y por escrito de los titulares del Copyright.
#
# Cualquier uso no autorizado será perseguido conforme a la Ley Federal
# del Derecho de Autor (México) y tratados internacionales aplicables.
# =============================================================================
import uuid

from django.conf import settings
from django.db import models


class SpeciesCatalog(models.Model):
    # Additional technical fields for the wiki
    habitat = models.TextField(null=True, blank=True)
    soil_type = models.TextField(null=True, blank=True)
    irrigation = models.TextField(null=True, blank=True)
    uses = models.TextField(null=True, blank=True)
    uv_rays = models.FloatField(null=True, blank=True)
    soil_humidity_min = models.FloatField(null=True, blank=True)
    soil_humidity_max = models.FloatField(null=True, blank=True)
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    scientific_name = models.TextField()
    common_name = models.TextField(null=True, blank=True)
    ideal_humidity_min = models.FloatField(null=True, blank=True)
    ideal_humidity_max = models.FloatField(null=True, blank=True)
    ideal_temp_min = models.FloatField(null=True, blank=True)
    ideal_temp_max = models.FloatField(null=True, blank=True)
    image_url = models.TextField(null=True, blank=True)
    ideal_ph_min = models.FloatField(null=True, blank=True)
    ideal_ph_max = models.FloatField(null=True, blank=True)
    ideal_ph_optimal = models.FloatField(null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    category = models.CharField(
        max_length=20,
        choices=[
            ('planta', 'Planta'),
            ('plaga', 'Plaga'),
            ('enfermedad', 'Enfermedad'),
        ],
        default='planta',
        db_index=True,
        help_text="Categoría taxonómica para filtrado en la Wiki.",
    )

    # NOM-059: Protección de flora silvestre mexicana
    is_protected_nom059 = models.BooleanField(
        default=False,
        help_text="Indica si la especie está protegida por NOM-059-SEMARNAT.",
    )
    protection_category = models.CharField(
        max_length=20,
        blank=True,
        choices=[
            ("P", "En peligro de extinción"),
            ("T", "Amenazada"),
            ("Pr", "Sujeta a protección especial"),
        ],
    )

    class Meta:
        db_table = "species_catalog"
        managed = True

    def __str__(self):
        return self.scientific_name


class UserPlant(models.Model):
    """
    Associates a user with a plant.
    The farmer creates a plant here and receives a UUID (plant_id)
    to configure on the ESP32 hardware for telemetry ingestion.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        db_column="user_id",
        related_name="plants",
    )
    species = models.ForeignKey(
        SpeciesCatalog,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        db_column="species_id",
    )
    nickname = models.TextField(null=True, blank=True)
    hardware_pin = models.CharField(max_length=10, null=True, blank=True, help_text="Pin físico del sensor en el nodo ESP32")

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "user_plants"
        managed = True
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.nickname} ({self.id})"


class FavoritePlant(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="favorite_plants",
    )
    plant = models.ForeignKey(
        UserPlant,
        on_delete=models.CASCADE,
        related_name="favorited_by",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "favorite_plants"
        unique_together = ("user", "plant")
        managed = True

    def __str__(self):
        return f"Fav: {self.user} -> {self.plant.id}"

# ---------------------------------------------------------------------------
# Flora – ficha técnico‑plaga/plantilla (admin)
# ---------------------------------------------------------------------------
class Flora(models.Model):
    """
    Ficha técnica de flora o plaga que incluye foto real.
    Relacionada al usuario que la crea (admin panel).
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='floras',
        null=False,
    )
    common_name = models.CharField(max_length=128, help_text='Nombre común')
    scientific_name = models.CharField(max_length=256, help_text='Nombre científico')
    family = models.CharField(max_length=128, blank=True, help_text='Familia taxonómica')
    treatment = models.TextField(blank=True, help_text='Método de tratamiento o control')
    image = models.ImageField(upload_to='flora_images/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'flora'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.common_name} ({self.scientific_name})"
