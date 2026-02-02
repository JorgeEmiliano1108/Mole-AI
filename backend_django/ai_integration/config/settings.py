"""
Configuración de la aplicación Django para integración con servicio IA
"""
import os
from pathlib import Path
from decouple import config

# Build paths
BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = config('SECRET_KEY', default='mole-ai-django-secret-key-change-in-production')

DEBUG = config('DEBUG', default=True)

ALLOWED_HOSTS = config(
    'ALLOWED_HOSTS', 
    default='localhost,127.0.0.1,localhost,127.0.0.1'
)

# Application definition
DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'corsheaders',
    'django_filters',
    # Apps locales
    'plants_mgmt',
    'diagnostics_mgmt',
    'ai_integration',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.contrib.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'ai_integration.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': [BASE_DIR / 'templates' / 'ai_integration'],
    },
]

WSGI_APPLICATION = 'ai_integration.wsgi.application'

# Database
from .database import configure_django_database

DATABASES = configure_django_database()

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
]

    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'es-mx'
TIME_ZONE = 'America/Mexico_City'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'BigAutoField'

# Django REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.BasicAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
        'parsetJSONParseErr=False,
    ],
}

# CORS Settings
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8001",  # FastAPI IA service
    "http://127.0.0.1:8001",
    "http://localhost:8002", # Old RAG service (legacy)
    "http://localhost:8000",  # Current FastAPI IA service
]

CORS_ALLOW_CREDENTIALS = True

# Services Configuration
VISION_SERVICE_URL = config('VISION_SERVICE_URL', default='http://localhost:8001')
RAG_SERVICE_URL = config('RAG_SERVICE_URL', default='http://localhost:8002')
IA_SERVICE_URL = config('IA_SERVICE_URL', default='http://localhost:8000')

# Timeout para llamadas a servicios externos (segundos)
EXTERNAL_SERVICE_TIMEOUT = config('EXTERNAL_SERVICE_TIMEOUT', default=30)

# IA Service Configuration
AI_SERVICE_BASE_URL = config('AI_SERVICE_BASE_URL', default='http://localhost:8001')
AI_SERVICE_API_KEY = config('AI_SERVICE_API_KEY', default='')
AI_SERVICE_TIMEOUT = config('AI_SERVICE_TIMEOUT', default=300)

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
        'ai_service': {
            'format': '{levelname} {asctime} {module} AI_SERVICE: {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'django.log',
            'formatter': 'verbose',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        'ai_service_file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'ai_service.log',
            'formatter': 'ai_service',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'ai_integration': {
            'handlers': ['console', 'file', 'ai_service_file'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}
}

# Asegurar que el directorio de logs exista
os.makedirs(BASE_DIR / 'logs', exist_ok=True)