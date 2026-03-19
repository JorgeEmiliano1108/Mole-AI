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
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404

from plants.infrastructure.repositories.models import UserPlant
from .serializers import PlantCreateSerializer, PlantUpdateSerializer, PlantResponseSerializer

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
