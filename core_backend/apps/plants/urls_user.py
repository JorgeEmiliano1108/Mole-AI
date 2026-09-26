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
from django.urls import path

from . import views

app_name = "user_plants"

urlpatterns = [
    path("my-collection/", views.my_collection_view, name="my_collection"),
    path("my-alerts/", views.my_alerts_view, name="my_alerts"),
    path("", views.plant_list_view, name="plant_list"),
    # NOTA: "favorites/" va ANTES de "<uuid:plant_id>/" por claridad.
    # (Django lo resolvía igual: el conversor UUID rechaza "favorites",
    # pero el orden explícito evita lecturas erróneas y futuros choques.)
    path("favorites/", views.favorite_plant_list_view, name="favorite_plant_list"),
    path("favorites/<int:fav_id>/", views.favorite_plant_detail_view, name="favorite_plant_detail"),
    path("<uuid:plant_id>/", views.plant_detail_view, name="plant_detail"),
]
