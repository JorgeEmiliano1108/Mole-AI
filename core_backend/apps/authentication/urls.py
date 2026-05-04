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

app_name = 'authentication'

urlpatterns = [
    # Local login (username/password)
    path('login/', views.login_view, name='login'),
    
    # Supabase JWT validation
    path('validate-token/', views.validate_token_view, name='validate_token'),

    # Local Registration endpoint for new Farmers
    path('register/', views.register_view, name='register'),

    # Email verification
    path('verify-email/<str:token>/', views.verify_email_view, name='verify_email'),
    path('resend-verification/', views.resend_verification_view, name='resend_verification'),

    # User Profile endpoints
    path('profile/', views.user_profile_view, name='user_profile'),
    
    # User Subscription endpoints
    path('subscription/', views.user_subscription_view, name='user_subscription'),
    
    # User Metadata endpoints
    path('metadata/', views.user_metadata_view, name='user_metadata'),
    
    # Logout endpoint
    path('logout/', views.logout_view, name='logout'),
    
    # Health Check endpoint
    path('health/', views.AuthHealthCheckView.as_view(), name='auth_health_check'),
    
    # Debug Auth endpoint
    path('debug/', views.auth_debug_view, name='auth_debug'),
]