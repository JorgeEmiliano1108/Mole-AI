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

app_name = "plants"

urlpatterns = [
    path("", views.plant_list_view, name="plant_list"),
    path("<uuid:plant_id>/", views.plant_detail_view, name="plant_detail"),
    path("favorites/", views.favorite_plant_list_view, name="favorite_plant_list"),
    path("favorites/<int:fav_id>/", views.favorite_plant_detail_view, name="favorite_plant_detail"),
]
