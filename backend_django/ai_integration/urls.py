"""
Mapeo de URLs para la aplicación de integración IA
"""
from django.urls import path
from . import views

app_name = 'ai_integration'

urlpatterns = [
    # Dashboard principal de IA
    path('', views.dashboard, name='ai_dashboard'),
    
    # Endpoints de diagnóstico con IA
    path('diagnose/', views.diagnose_plant, name='diagnose_plant'),
    path('diagnose/batch/', views.batch_diagnose, name='batch_diagnose'),
    
    # Endpoint de chat con IA
    path('chat/', views.ai_chat, name='ai_chat'),
    
    # Health check del servicio IA
    path('health/', views.ai_health_check, name='ai_health_check'),
    
    # Plantillas HTML
    path('interface/', views.ai_interface, name='ai_interface'),
]