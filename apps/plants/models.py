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

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "user_plants"
        managed = True
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.nickname} ({self.id})"


# ------ IMPORTANTE: DESCOMENTAR ESTO DESPUÉS DEL PRIMER FAKE-INITIAL ------
# class FavoritePlant(models.Model):
#     id = models.BigAutoField(primary_key=True)
#     user = models.ForeignKey(
#         settings.AUTH_USER_MODEL,
#         on_delete=models.CASCADE,
#         related_name="favorite_plants",
#     )
#     plant = models.ForeignKey(
#         UserPlant,
#         on_delete=models.CASCADE,
#         related_name="favorited_by",
#     )
#     created_at = models.DateTimeField(auto_now_add=True)
# 
#     class Meta:
#         db_table = "favorite_plants"
#         unique_together = ("user", "plant")
#         managed = True
# 
#     def __str__(self):
#         return f"Fav: {self.user} -> {self.plant.id}"
