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

app_name = 'ai_models'

urlpatterns = [
    # LLM Request endpoints
    path('llm/requests/', views.llm_requests_view, name='llm_requests'),
    
    # CNN Inference endpoints
    path('cnn/inferences/', views.cnn_inferences_view, name='cnn_inferences'),
    
    # Model Performance endpoints
    path('performance/', views.model_performance_view, name='model_performance'),
    
    # AI Model Configuration endpoints
    path('config/', views.ai_model_config_view, name='ai_model_config'),
    
    # AI Training endpoints
    path('train/rag/', views.train_rag_view, name='train_rag'),
    path('train/vision/', views.train_vision_view, name='train_vision'),
    
    # Health Check endpoint
    path('health/', views.AIHealthCheckView.as_view(), name='ai_health_check'),
    
    # AI Vision End-to-End endpoints
    path('vision/analyze/', views.analyze_vision_view, name='analyze_vision'),
    path('vision/status/<str:task_id>/', views.vision_task_status_view, name='vision_task_status'),
]