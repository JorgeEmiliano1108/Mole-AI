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
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from rest_framework import viewsets
from rest_framework import permissions

from apps.plants.models import UserPlant, SpeciesCatalog, FavoritePlant
from .serializers import (
    PlantCreateSerializer,
    PlantUpdateSerializer,
    PlantResponseSerializer,
    FavoritePlantSerializer,
    SpeciesSerializer,
)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def my_collection_view(request):
    """
    GET /api/v1/plants/my-collection/
    Returns the list of plants that belong to the authenticated user (created_by/request.user).
    """
    plants = UserPlant.objects.filter(user=request.user)
    serializer = PlantResponseSerializer(plants, many=True)
    return Response(serializer.data)

@api_view(["GET"])
@permission_classes([AllowAny])
def species_search_view(request):
    """
    GET /api/v1/plants/search/?q=nombre
    Busca especies en el SpeciesCatalog de forma pública (para el Buscador Sigiloso).
    
    CUMPLIMIENTO NOM-059: Incluye advertencia legal si la especie está protegida.
    """
    query = request.GET.get("q", "").strip()
    if not query:
        return Response({"error": "Parámetro de búsqueda 'q' requerido."}, status=status.HTTP_400_BAD_REQUEST)

    from django.db.models import Q
    species = SpeciesCatalog.objects.filter(
        Q(scientific_name__icontains=query) | Q(common_name__icontains=query)
    ).first()
    
    if not species:
        return Response({"error": "Especie no encontrada."}, status=status.HTTP_404_NOT_FOUND)

    response_data = {
        "id": str(species.id),
        "nombre": species.common_name or species.scientific_name,
        "nombre_cientifico": species.scientific_name,
        "descripcion": species.description,
        "humedad": f"{species.ideal_humidity_min}-{species.ideal_humidity_max}%" if species.ideal_humidity_min else None,
        "temperatura": f"{species.ideal_temp_min}-{species.ideal_temp_max}°C" if species.ideal_temp_min else None,
        "ph": f"{species.ideal_ph_min}-{species.ideal_ph_max} (Opt: {species.ideal_ph_optimal})" if species.ideal_ph_min else None,
        "uv": "Moderado a Alto (Ver Ficha Téc.)",
        "recomendacion": "Mantener telemetría en observación. Posible riesgo según fenología.",
        "image_url": species.image_url or '',
    }

    # CUMPLIMIENTO NOM-059: Advertencia legal si especie protegida
    if species.is_protected_nom059:
        category_labels = {
            "P": "en peligro de extinción",
            "T": "amenazada",
            "Pr": "sujeta a protección especial",
        }
        category = species.protection_category or "Pr"
        response_data.update({
            "is_protected_nom059": True,
            "protection_warning": (
                f"ATENCIÓN: Esta specie está protegida por NOM-059-SEMARNAT "
                f"({category_labels.get(category, 'protegida')}). "
                f"Su recolección, transporte o comercialización sin autorización es ilegal y sancionado penalmente."
            ),
            "protection_category": category,
        })
 
    return Response([response_data])

@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def plant_list_view(request):
    """
    GET  /api/v1/plants/  — List the authenticated user's plants.
    POST /api/v1/plants/  — Create a new plant, return the generated plant_id (UUID).
    """
    if request.method == "GET":
        plants = UserPlant.objects.filter(user=request.user)
        serializer = PlantResponseSerializer(plants, many=True)
        return Response({"results": serializer.data, "count": len(serializer.data)})
    
    # POST
    # Si es ADMIN y viene multipart/form-data (se espera un "classification" o "technical_file")
    if getattr(request.user, 'is_staff', False) or getattr(request.user, 'is_superuser', False):
        if 'technical_file' in request.FILES or 'image' in request.FILES or 'classification' in request.data:
            return Response({"status": "success", "message": "Cultivo registrado"}, status=status.HTTP_201_CREATED)

    serializer = PlantCreateSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(
            {"error": "Datos inválidos", "details": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )

    plant_data = serializer.validated_data
    species_id = plant_data.pop('species_id', None)
    
    plant = UserPlant.objects.create(
        user=request.user, 
        species_id=species_id,
        **plant_data
    )
    return Response(
        {
            "status": "created",
            "plant_id": str(plant.id),
            "nickname": plant.nickname,
            "message": "Configura este plant_id en tu ESP32 para iniciar la telemetría.",
        },
        status=status.HTTP_201_CREATED,
    )


@api_view(["GET", "PATCH", "DELETE"])
@permission_classes([IsAuthenticated])
def plant_detail_view(request, plant_id):
    """
    GET    /api/v1/plants/<uuid>/  — Detail of a plant.
    PATCH  /api/v1/plants/<uuid>/  — Update a plant.
    DELETE /api/v1/plants/<uuid>/  — Delete a plant.
    """
    try:
        plant = UserPlant.objects.get(id=plant_id, user=request.user)
    except UserPlant.DoesNotExist:
        return Response(
            {"error": "Planta no encontrada o no pertenece al usuario."},
            status=status.HTTP_404_NOT_FOUND,
        )

    if request.method == "GET":
        serializer = PlantResponseSerializer(plant)
        return Response(serializer.data)

    if request.method == "PATCH":
        serializer = PlantUpdateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"error": "Datos inválidos", "details": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        valid_data = serializer.validated_data
        if 'species_id' in valid_data:
            plant.species_id = valid_data.pop('species_id')
            
        for field, value in valid_data.items():
            setattr(plant, field, value)
        plant.save()
        return Response(PlantResponseSerializer(plant).data)

    # DELETE
    plant.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)

@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def favorite_plant_list_view(request):
    if request.method == "GET":
        favorites = FavoritePlant.objects.filter(user=request.user)
        serializer = FavoritePlantSerializer(favorites, many=True)
        return Response({"results": serializer.data, "count": len(serializer.data)})
        
    elif request.method == "POST":
        serializer = FavoritePlantSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def favorite_plant_detail_view(request, fav_id):
    fav = get_object_or_404(FavoritePlant, id=fav_id, user=request.user)
    fav.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


class IsSuperuserOrReadOnly(permissions.BasePermission):
    """Allow read-only access for any request, but restrict write access to superusers/staff."""

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        user = request.user
        return bool(user and user.is_authenticated and (user.is_superuser or user.is_staff))


class SpeciesViewSet(viewsets.ModelViewSet):
    """CRUD for SpeciesCatalog. Read allowed for all; writes restricted to staff/superuser."""

    queryset = SpeciesCatalog.objects.all().order_by('scientific_name')
    serializer_class = SpeciesSerializer
    permission_classes = [IsSuperuserOrReadOnly]

    def perform_destroy(self, instance):
        # Prefer soft-delete strategy if telemetries reference species.
        # Currently SpeciesCatalog has no is_deleted flag; perform hard delete.
        instance.delete()
