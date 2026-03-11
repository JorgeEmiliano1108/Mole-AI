from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

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

    plant = UserPlant.objects.create(user=request.user, **serializer.validated_data)
    return Response(
        {
            "status": "created",
            "plant_id": str(plant.id),
            "name": plant.name,
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
        for field, value in serializer.validated_data.items():
            setattr(plant, field, value)
        plant.save()
        return Response(PlantResponseSerializer(plant).data)

    # DELETE
    plant.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)
