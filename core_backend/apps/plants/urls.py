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
from rest_framework.routers import DefaultRouter
from . import views

app_name = "plants"

urlpatterns = [
    path("", views.plant_list_view, name="plant_list"),  # GET/POST /api/v1/plants/
    path("search/", views.species_search_view, name="species_search"),
    path("flora/", views.flora_create_view, name="flora_create"),
]

# Register species router (CRUD surface)
router = DefaultRouter()
router.register(r'species', views.SpeciesViewSet, basename='species')

urlpatterns += router.urls
