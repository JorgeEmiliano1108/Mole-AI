from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework import status
import logging
import requests
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

logger = logging.getLogger(__name__)

from apps.core.models import FeedbackTicket, SensorLog
from apps.plants.models import UserPlant

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
        logger.exception("Error checking status ms3: %s", e)
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


def _role_of(user):
    if user.is_superuser:
        return "Superadmin"
    if user.is_staff:
        return "Admin"
    return "Operador"


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdminUser])
def admin_users_list_view(request):
    """
    GET /api/v1/admin/users/?search=&role=&page= — Tabla usuarios (issue 16).

    `role` admite Operador|Admin|Superadmin (case-insensitive) y se resuelve
    a nivel ORM: Superadmin → is_superuser, Admin → staff no-superuser,
    Operador → ni staff ni superuser. Sin N+1 ni filtrado en memoria.
    """
    from django.core.paginator import Paginator
    from django.db.models import Q
    User = get_user_model()
    qs = User.objects.all().order_by('-date_joined')
    search = (request.query_params.get('search') or '').strip()
    if search:
        qs = qs.filter(Q(username__icontains=search) | Q(email__icontains=search))
    role = (request.query_params.get('role') or '').strip().lower()
    if role == 'superadmin':
        qs = qs.filter(is_superuser=True)
    elif role == 'admin':
        qs = qs.filter(is_staff=True, is_superuser=False)
    elif role == 'operador':
        qs = qs.filter(is_staff=False, is_superuser=False)
    total = qs.count()
    try:
        page_num = max(1, int(request.query_params.get('page', 1)))
    except (TypeError, ValueError):
        page_num = 1
    items = Paginator(qs, 50).get_page(page_num).object_list
    return Response({
        "count": total,
        "results": [{
            "id": u.id, "username": u.username, "email": u.email,
            "role": _role_of(u), "is_active": u.is_active,
            "is_premium": getattr(u, 'is_premium', False),
            "date_joined": u.date_joined,
        } for u in items],
    })


@api_view(['GET', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated, IsAdminUser])
def admin_user_detail_view(request, user_id):
    """
    GET/PATCH/DELETE /api/v1/admin/users/<id>/ — Gestiona rol y estado.
    PATCH admite {role: Operador|Admin|Superadmin, is_active: bool}.
    DELETE desactiva (soft, nunca borra: preserva auditoría).
    """
    from apps.core.models import AuditLog
    User = get_user_model()
    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        return Response({"error": "No existe."}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        return Response({
            "id": user.id, "username": user.username, "email": user.email,
            "role": _role_of(user), "is_active": user.is_active,
            "is_premium": getattr(user, 'is_premium', False),
            "data_consent": getattr(user, 'data_consent', None),
            "date_joined": user.date_joined,
        })

    if request.method == 'DELETE':
        if user.is_superuser and not request.user.is_superuser:
            return Response({"error": "Solo Superadmin desactiva Superadmin."},
                            status=status.HTTP_403_FORBIDDEN)
        user.is_active = False
        user.save(update_fields=["is_active"])
        AuditLog.objects.create(
            user_id=request.user.id, action="ADMIN_DEACTIVATE",
            ip_address=request.META.get("REMOTE_ADDR"),
            details=f"Desactivado user_id={user.id}.",
        )
        return Response({"status": "deactivated"})

    # PATCH
    role = request.data.get('role')
    if role is not None:
        if role not in ('Operador', 'Admin', 'Superadmin'):
            return Response({"error": "Rol inválido."}, status=status.HTTP_400_BAD_REQUEST)
        if role == 'Superadmin' and not request.user.is_superuser:
            return Response({"error": "Solo Superadmin otorga Superadmin."},
                            status=status.HTTP_403_FORBIDDEN)
        user.is_staff = role in ('Admin', 'Superadmin')
        user.is_superuser = (role == 'Superadmin')
    if 'is_active' in request.data:
        if user.is_superuser and not request.user.is_superuser:
            return Response({"error": "Solo Superadmin toca Superadmin."},
                            status=status.HTTP_403_FORBIDDEN)
        user.is_active = bool(request.data.get('is_active'))
    user.save()
    AuditLog.objects.create(
        user_id=request.user.id, action="ADMIN_UPDATE_USER",
        ip_address=request.META.get("REMOTE_ADDR"),
        details=f"Actualizado user_id={user.id} role={_role_of(user)} active={user.is_active}.",
    )
    return Response({"status": "updated", "role": _role_of(user),
                     "is_active": user.is_active})

@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdminUser])
def live_alerts_view(request):
    """
    Devuelve un JSON con las alertas en vivo (Telemetría) para el Dashboard Admin.
    Lee el esquema vivo 1:N (`AmbientReading` + `SoilReading` vía bindings);
    si está vacío, cae a `SensorLog` legacy. Cada alerta lleva identificadores
    estructurados para la app (issue 16).
    """
    from apps.core.models import AmbientReading, SoilReading
    alerts = []

    def push(tipo, msg, source, recorded_at, device_id=None, plant_id=None):
        alerts.append({
            "tipo": tipo, "msg": msg, "source": source,
            "recorded_at": recorded_at.isoformat() if recorded_at else None,
            "device_id": str(device_id) if device_id else None,
            "plant_id": str(plant_id) if plant_id else None,
        })

    soils = (SoilReading.objects.select_related("binding__device", "binding__plant")
             .order_by('-recorded_at')[:20])
    for s in soils:
        dev = s.binding.device if s.binding else None
        pid = s.binding.plant_id if s.binding else None
        if s.soil_humidity is not None and s.soil_humidity < 20.0:
            push("error", f"Humedad por debajo del umbral crítico ({s.soil_humidity}%)",
                 "soil", s.recorded_at, getattr(dev, 'id', None), pid)
        elif s.soil_humidity is not None and s.soil_humidity < 35.0:
            push("warn", f"Humedad baja detectada ({s.soil_humidity}%)",
                 "soil", s.recorded_at, getattr(dev, 'id', None), pid)

    ambients = AmbientReading.objects.select_related("device").order_by('-recorded_at')[:20]
    for a in ambients:
        if a.air_temperature is not None and a.air_temperature > 30.0:
            push("warn", f"Fluctuación térmica detectada ({a.air_temperature}°C)",
                 "ambient", a.recorded_at, a.device_id)
        if a.uv_index is not None and a.uv_index > 8.0:
            push("error", f"Índice UV peligroso detectado ({a.uv_index})",
                 "ambient", a.recorded_at, a.device_id)

    if not alerts:
        # Fallback legacy: SensorLog congelado (A3) para flotas viejas.
        for log in SensorLog.objects.order_by('-recorded_at')[:5]:
            if log.soil_humidity is not None and log.soil_humidity < 20.0:
                push("error", f"Humedad por debajo del umbral crítico ({log.soil_humidity}%)",
                     "sensorlog", log.recorded_at, None, str(log.plant_id))
            elif log.soil_humidity is not None and log.soil_humidity < 35.0:
                push("warn", f"Humedad baja detectada ({log.soil_humidity}%)",
                     "sensorlog", log.recorded_at, None, str(log.plant_id))
            if log.air_temperature is not None and log.air_temperature > 30.0:
                push("warn", f"Fluctuación térmica detectada ({log.air_temperature}°C)",
                     "sensorlog", log.recorded_at, None, str(log.plant_id))
            if log.uv_index is not None and log.uv_index > 8.0:
                push("error", f"Índice UV peligroso detectado ({log.uv_index})",
                     "sensorlog", log.recorded_at, None, str(log.plant_id))

    # Si no hay alertas críticas/warnings, proveer información de estado
    if not alerts:
        alerts.append({
            "msg": "Monitor Vital estable. Biomasa operando dentro de umbrales.",
            "tipo": "info"
        })

    # Limitar la salida a los primeros 5 eventos más relevantes
    return Response({"alerts": alerts[:5]})
