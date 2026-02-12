from django.urls import path
from . import views
from apps.core.api_views import mock_sensor_data

app_name = 'core'

urlpatterns = [
    # Vista principal
    path('', views.index_view, name='index'),
    
    # API endpoints
    path('api/v1/sensor-data/', views.sensor_data_view, name='sensor_data'),
    path('api/v1/sensor-data/latest/', mock_sensor_data, name='mock_sensor'),
    path('api/v1/sensor-logs/', views.sensor_log_view, name='sensor_log'),
    path('api/v1/diagnostics/', views.diagnostic_view, name='diagnostic'),
    path('api/v1/diagnostics/history/', views.diagnostic_history_view, name='diagnostic_history'),
    path('api/v1/plant-knowledge/', views.plant_knowledge_view, name='plant_knowledge'),
    path('api/v1/llm/chat/', views.llm_chat_view, name='llm_chat'),
    path('api/v1/health/', views.health_check_view, name='health_check'),
]