from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework import status
import uuid
import requests
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

from apps.core.models import FeedbackTicket, SensorLog
from apps.plants.models import UserPlant
from django.db.models import Avg, Count

from celery.result import AsyncResult

User = get_user_model()

@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdminUser])
def admin_stats_view(request):
    """
    Devuelve un JSON con estadísticas reales de la BD
    """
    now = timezone.now()
    active_users = User.objects.filter(is_active=True).count()
    inactive_users = User.objects.filter(is_active=False).count()
    total_plants = UserPlant.objects.count()
    
    regs = []
    for i in range(6, -1, -1):
        day_start = (now - timedelta(days=i)).replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)
        count = User.objects.filter(date_joined__gte=day_start, date_joined__lt=day_end).count()
        regs.append(count)
        
    from django.db import connection
    with connection.cursor() as cursor:
        cursor.execute("SELECT avg_hum, avg_temp, avg_uv, avg_ph FROM admin_stats LIMIT 1;")
        row = cursor.fetchone()

    if row:
        aggs = {
            'avg_hum': row[0],
            'avg_temp': row[1],
            'avg_uv': row[2],
            'avg_ph': row[3]
        }
    else:
        aggs = {
            'avg_hum': None,
            'avg_temp': None,
            'avg_uv': None,
            'avg_ph': None
        }
    # Validation strictly as requested: if table is empty, return 0 or []
    if all(v is None for v in aggs.values()):
        health = [0, 0, 0, 0, 0]
    else:
        avg_hum = aggs['avg_hum'] or 0
        avg_temp = aggs['avg_temp'] or 0
        avg_uv = aggs['avg_uv'] or 0
        avg_ph = aggs['avg_ph'] or 0
        # Removing the mock '90' and replacing it with 0
        health = [
            min(100, max(0, avg_hum)),
            min(100, max(0, avg_temp)),
            0,  # No real nutrient data available, substituting mock with 0
            min(100, max(0, avg_uv * 10)),
            min(100, max(0, avg_ph * 10))
        ]

    return Response({
        "users": [active_users, inactive_users, 0],
        "regs": regs,
        "health": health,
        "total_plants": total_plants
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdminUser])
def admin_report_text_view(request):
    """
    Devuelve las estadísticas básicas como JSON para que el frontend genere el TXT
    """
    active_users = User.objects.filter(is_active=True).count()
    inactive_users = User.objects.filter(is_active=False).count()
    total_plants = UserPlant.objects.count()
    # Identificar plantas críticas (por ejemplo, con un sensor log reciente reportando baja humedad)
    from apps.core.models import SensorLog
    plantas_criticas = SensorLog.objects.filter(soil_humidity__lt=20).values('plant_id').distinct().count()
    
    return Response({
        "total_usuarios": active_users + inactive_users,
        "plantas_criticas": plantas_criticas
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdminUser])
def intercepted_reports_view(request):
    """
    Devuelve los últimos reportes interceptados
    """
    tickets = FeedbackTicket.objects.order_by('-created_at')[:20]
    res = []
    for t in tickets:
        res.append({
            "time": t.created_at.strftime("%H:%M"),
            "user": t.user.username if t.user else "Sistema",
            "type": t.topic,
            "message": t.message
        })
    return Response(res)

@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdminUser])
def master_report_view(request):
    """
    Llama a Celery generar_master_report_task.delay()
    """
    try:
        resp = requests.post(
            'http://ms3_reports:8003/api/v1/reports/generate', 
            json={"date_range_days": 90, "sensors": []}, 
            timeout=5
        )
        if resp.status_code == 200:
            return Response({"job_id": resp.json().get("job_id"), "status": "processing"}, status=status.HTTP_202_ACCEPTED)
        return Response({"job_id": None, "status": "failed"}, status=500)
    except Exception as e:
        logger.error(f"Error calling ms3: {e}")
        return Response({"job_id": None, "status": "failed"}, status=500)

@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdminUser])
def master_report_status_view(request, job_id):
    """
    Consulta a Celery AsyncResult
    """
    try:
        resp = requests.get(f'http://ms3_reports:8003/api/v1/reports/{job_id}/status', timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            if data.get("status") == "SUCCESS":
                d_resp = requests.get(f'http://ms3_reports:8003/api/v1/reports/{job_id}/download', timeout=5)
                if d_resp.status_code == 200:
                    return Response({"status": "completed", "file_url": d_resp.json().get("download_url")})
                return Response({"status": "completed", "file_url": ""})
            elif data.get("status") == "FAILED":
                return Response({"status": "failed"})
            return Response({"status": "processing"})
        return Response({"status": "failed"}, status=500)
    except Exception as e:
        print(f"Error checking status ms3: {e}")
        return Response({"status": "failed"}, status=500)

@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdminUser])
def admin_users_create_view(request):
    """
    Crea un usuario real usando el gestor de Django
    """
    data = request.data
    username = data.get('username')
    password = data.get('password')
    role = data.get('role', 'Operador')
    
    if not username or not password:
        return Response({"status": "error", "message": "Faltan datos"}, status=status.HTTP_400_BAD_REQUEST)
        
    if User.objects.filter(username=username).exists():
        return Response({"status": "error", "message": "Usuario ya existe"}, status=status.HTTP_400_BAD_REQUEST)
    
    user = User.objects.create_user(username=username, password=password)
    
    # Simple RBAC Mapping based on role string given by Frontend
    if role == 'Admin' or role == 'Superadmin':
        user.is_staff = True
        user.is_superuser = True
    elif role == 'Agrónomo':
        user.is_staff = True
    
    user.save()
    
    return Response({"status": "success", "message": f"Usuario {username} creado con rol {role}"}, status=status.HTTP_201_CREATED)

@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdminUser])
def live_alerts_view(request):
    """
    Devuelve un JSON con las alertas en vivo (Telemetría) para el Dashboard Admin.
    Reemplaza los mocks estáticos leyendo eventos recientes.
    """
    logs = SensorLog.objects.order_by('-recorded_at')[:5]
    alerts = []
    for log in logs:
        # Generar alerta si la humedad del suelo está baja
        if log.soil_humidity is not None and log.soil_humidity < 20.0:
            alerts.append({
                "msg": f"Humedad por debajo del umbral crítico ({log.soil_humidity}%)",
                "tipo": "error"
            })
        elif log.soil_humidity is not None and log.soil_humidity < 35.0:
            alerts.append({
                "msg": f"Humedad baja detectada ({log.soil_humidity}%)",
                "tipo": "warn"
            })
            
        # Generar alerta si la temperatura es alta
        if log.air_temperature is not None and log.air_temperature > 30.0:
            alerts.append({
                "msg": f"Fluctuación térmica detectada ({log.air_temperature}°C)",
                "tipo": "warn"
            })
            
        # Generar alerta si el UV es alto
        if log.uv_index is not None and log.uv_index > 8.0:
            alerts.append({
                "msg": f"Índice UV peligroso detectado ({log.uv_index})",
                "tipo": "error"
            })
            
    # Si no hay alertas críticas/warnings, proveer información de estado
    if not alerts:
        alerts.append({
            "msg": "Monitor Vital estable. Biomasa operando dentro de umbrales.",
            "tipo": "info"
        })
        
    # Limitar la salida a los primeros 5 eventos más relevantes
    return Response({"alerts": alerts[:5]})
