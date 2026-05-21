# =============================================================================
# Copyright (C) 2024-2026 Mole.AI — All Rights Reserved.
# =============================================================================
from django.urls import path
from . import views
from apps.core import admin_views
from apps.core.api_views import (
    mock_sensor_data, telemetry_latest_view, sensors_ingest_view,
    device_health_view, device_bindings_view, device_binding_delete_view,
)

app_name = 'core'

urlpatterns = [
    # Telemetría
    path('sensor-data/', views.sensor_data_view, name='sensor_data'),
    path('sensor-data/batch/', views.sensor_batch_view, name='sensor_batch'),
    path('sensor-data/edge-batch/', views.EdgeNodeIngestView.as_view(), name='edge_ingest_batch'),
    path('sensor-data/<int:pk>/', views.sensor_data_patch_view, name='sensor_data_patch'),
    path('sensor-data/latest/', mock_sensor_data, name='mock_sensor'),
    path('telemetry/latest/', telemetry_latest_view, name='telemetry_latest'),
    path('sensors/ingest', sensors_ingest_view, name='sensors_ingest'),
    path('sensor-logs/', views.sensor_log_view, name='sensor_log'),
    path('devices/<uuid:id>/health/', device_health_view, name='device_health'),
    path('devices/<uuid:id>/bindings/', device_bindings_view, name='device_bindings'),
    path('devices/<uuid:id>/bindings/<int:binding_id>/', device_binding_delete_view, name='device_binding_delete'),

    # IA y Diagnósticos
    path('diagnostics/', views.diagnostic_view, name='diagnostic'),
    path('diagnostics/history/', views.diagnostic_history_view, name='diagnostic_history'),
    path('diagnostics/<uuid:id>/download/', views.download_diagnostic_pdf, name='diagnostic_download'),
    
    # Mapas
    path('map/hotspots/', views.map_hotspots_view, name='map_hotspots'),
    path('weather/tile/<str:layer>/<int:z>/<int:x>/<int:y>.png', views.openweather_tile_proxy, name='weather_tile_proxy'),
    path('weather/current/', views.current_weather_proxy, name='current_weather_proxy'),
    path('diagnosticos/geolocalizados/', views.diagnosticos_geolocalizados_list, name='geo_list'),
    path('diagnosticos/geolocalizados/create/', views.diagnosticos_geolocalizados_create, name='geo_create'),
    # IoT node creation endpoint
    path('iot/nodes/', views.iot_node_create, name='iot_node_create'),
    
    # Conocimiento y Chat
    path('plant-knowledge/', views.plant_knowledge_view, name='plant_knowledge'),
    path('llm/chat/', views.llm_chat_view, name='llm_chat'),
    path('chat/fallback/', views.chat_fallback_view, name='chat_fallback'),
    path('chat/history/', views.chat_history_view, name='chat_history'),
    
    # Sistema
    path('health/', views.health_check_view, name='health_check'),
    path('fichas/', views.fichas_public_view, name='fichas_public'),
    path('history/', views.consolidated_history_view, name='consolidated_history'),
    path('feedback/', views.feedback_create_view, name='feedback_create'),

    # Admin Panel (Estadísticas y Reportes)
    path('admin/statistics', admin_views.admin_stats_view, name='admin_stats'),
    path('admin/report-text', admin_views.admin_report_text_view, name='admin_report_text'),
    path('admin/users/create/', admin_views.admin_users_create_view, name='admin_users_create'),
    path('admin/live-alerts', admin_views.live_alerts_view, name='live_alerts'),
    path('admin/reports/generate', admin_views.master_report_view, name='admin_report_generate'),
    path('admin/reports/<str:job_id>/status', admin_views.master_report_status_view, name='admin_report_status'),
    
    # Reportes
    path('reports/users', admin_views.intercepted_reports_view, name='reports_users'),
    path('reports/plants', views.sensor_log_view, name='reports_plants'),

    # Polling genérico de tareas asíncronas (Fase 2)
    path('tasks/status/<str:task_id>/', views.task_status_view, name='task_status'),
]