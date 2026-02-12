from django.urls import path
from . import views

app_name = 'ai_models'

urlpatterns = [
    # LLM Request endpoints
    path('api/v1/ai/llm/requests/', views.llm_requests_view, name='llm_requests'),
    
    # CNN Inference endpoints
    path('api/v1/ai/cnn/inferences/', views.cnn_inferences_view, name='cnn_inferences'),
    
    # Model Performance endpoints
    path('api/v1/ai/performance/', views.model_performance_view, name='model_performance'),
    
    # AI Model Configuration endpoints
    path('api/v1/ai/config/', views.ai_model_config_view, name='ai_model_config'),
    
    # Health Check endpoint
    path('api/v1/ai/health/', views.AIHealthCheckView.as_view(), name='ai_health_check'),
]