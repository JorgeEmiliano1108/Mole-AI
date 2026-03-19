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
from apps.core.api_views import mock_sensor_data

app_name = 'core'

urlpatterns = [
    # API endpoints — specific paths MUST be listed before generic to avoid URL shadowing
    path('sensor-data/batch/', views.sensor_batch_view, name='sensor_batch'),
    path('sensor-data/<int:pk>/', views.sensor_data_patch_view, name='sensor_data_patch'),
    path('sensor-data/', views.sensor_data_view, name='sensor_data'),
    path('sensor-data/latest/', mock_sensor_data, name='mock_sensor'),
    path('sensor-logs/', views.sensor_log_view, name='sensor_log'),
    path('diagnostics/', views.diagnostic_view, name='diagnostic'),
    path('diagnostics/<uuid:id>/download/', views.download_diagnostic_pdf, name='diagnostic_download'),
    path('diagnostics/history/', views.diagnostic_history_view, name='diagnostic_history'),
    path('diagnosticos/geolocalizados/', views.diagnosticos_geolocalizados_list, name='diagnosticos_geolocalizados_list'),
    path('diagnosticos/geolocalizados/create/', views.diagnosticos_geolocalizados_create, name='diagnosticos_geolocalizados_create'),
    path('map/hotspots/', views.map_hotspots_view, name='map_hotspots'),
    path('plant-knowledge/', views.plant_knowledge_view, name='plant_knowledge'),
    path('llm/chat/', views.llm_chat_view, name='llm_chat'),
    path('chat/fallback/', views.chat_fallback_view, name='chat_fallback'),
    path('health/', views.health_check_view, name='health_check'),
    path('history/', views.consolidated_history_view, name='history'),  # Endpoint consolidado
    path('feedback/', views.feedback_create_view, name='feedback_create'),
]