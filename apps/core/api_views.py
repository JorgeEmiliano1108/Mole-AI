from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
import random

@api_view(['GET'])
@permission_classes([AllowAny])
def mock_sensor_data(request):
    # Simulación para calmar al Frontend
    return JsonResponse({
        "temperature": round(random.uniform(20.0, 30.0), 1),
        "humidity": random.randint(40, 60),
        "soil_ph": round(random.uniform(6.0, 7.5), 1),
        "uv_index": random.randint(1, 5),
        "health_status": "OPTIMAL",
        "irrigation_active": False,
        "lights_active": True
    })