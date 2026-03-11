import uuid

from django.conf import settings
from django.db import models


class UserPlant(models.Model):
    """
    Associates a user with a plant.
    The farmer creates a plant here and receives a UUID (plant_id)
    to configure on the ESP32 hardware for telemetry ingestion.

    Maps to existing user_plants table in Supabase (managed=False).
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="plants",
    )
    name = models.CharField(max_length=150)
    species = models.CharField(max_length=150, blank=True, default="")
    location = models.CharField(max_length=255, blank=True, default="")
    notes = models.TextField(blank=True, default="")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "user_plants"
        managed = False
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} ({self.id})"
