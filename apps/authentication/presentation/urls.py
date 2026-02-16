from django.urls import path
from . import views

app_name = 'authentication'

urlpatterns = [
    # User Profile endpoints
    path('api/v1/auth/profile/', views.user_profile_view, name='user_profile'),
    
    # User Subscription endpoints
    path('api/v1/auth/subscription/', views.user_subscription_view, name='user_subscription'),
    
    # User Metadata endpoints
    path('api/v1/auth/metadata/', views.user_metadata_view, name='user_metadata'),
    
    # Logout endpoint
    path('api/v1/auth/logout/', views.logout_view, name='logout'),
    
    # Health Check endpoint
    path('api/v1/auth/health/', views.AuthHealthCheckView.as_view(), name='auth_health_check'),
    
    # Debug Auth endpoint
    path('api/v1/auth/debug/', views.auth_debug_view, name='auth_debug'),
]