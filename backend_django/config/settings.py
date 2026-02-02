import os
from pathlib import Path
from decouple import config

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = config('SECRET_KEY', default='mole-ai-secret-key-change-in-production')

DEBUG = config('DEBUG', default=True, cast=bool)

ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1', cast=lambda v: [s.strip() for s in v.split(',')])

DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

THIRD_PARTY_APPS = [
    'rest_framework',
    'corsheaders',
]

LOCAL_APPS = [
    'plants_mgmt',
    'diagnostics_mgmt',
    'ai_integration',
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    # Enterprise database monitoring middleware
    'config.middleware.DatabasePerformanceMiddleware',
    'config.middleware.DatabaseAnalyticsMiddleware',
    'config.middleware.DatabaseHealthCheckMiddleware',
    'config.middleware.DatabaseMetricsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# Enterprise-grade Database Configuration with Connection Pooling
from .database import configure_django_database

DATABASES = configure_django_database()

# Additional database performance settings
DATABASE_POOL_SETTINGS = {
    'MIN_CONNECTIONS': config('DB_MIN_CONNECTIONS', default=10, cast=int),
    'MAX_CONNECTIONS': config('DB_MAX_CONNECTIONS', default=100, cast=int),
    'CONNECTION_TIMEOUT': config('DB_CONNECTION_TIMEOUT', default=30.0, cast=float),
    'IDLE_TIMEOUT': config('DB_IDLE_TIMEOUT', default=600.0, cast=float),
    'MAX_LIFETIME': config('DB_MAX_LIFETIME', default=3600.0, cast=float),
}

# Database health monitoring
DB_HEALTH_MONITORING = config('DB_HEALTH_MONITORING', default=True, cast=bool)
DB_HEALTH_CHECK_INTERVAL = config('DB_HEALTH_CHECK_INTERVAL', default=60, cast=int)

# Performance optimization settings
DB_OPTIMIZATIONS = {
    'ENABLE_QUERY_CACHE': config('DB_ENABLE_QUERY_CACHE', default=True, cast=bool),
    'SLOW_QUERY_THRESHOLD': config('DB_SLOW_QUERY_THRESHOLD', default=1000, cast=int),  # ms
    'EXPLAIN_ANALYZE': config('DB_EXPLAIN_ANALYZE', default=False, cast=bool),
    'MAX_QUERY_TIME': config('DB_MAX_QUERY_TIME', default=5000, cast=int),  # ms
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
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
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

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
        'rest_framework.parsers.MultiPartParser',
        'rest_framework.parsers.FormParser',
    ],
}

# CORS Settings
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8001",
    "http://127.0.0.1:8001",
    "http://localhost:8002",
    "http://127.0.0.1:8002",
]

CORS_ALLOW_CREDENTIALS = True

# Servicios de IA
VISION_SERVICE_URL = config('VISION_SERVICE_URL', default='http://localhost:8001')
RAG_SERVICE_URL = config('RAG_SERVICE_URL', default='http://localhost:8002')

# Timeout para llamadas a servicios externos (segundos)
EXTERNAL_SERVICE_TIMEOUT = config('EXTERNAL_SERVICE_TIMEOUT', default=30, cast=int)

# Enterprise Logging with Database Performance Monitoring
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
        'performance': {
            'format': '{levelname} {asctime} {module} QUERY_TIME={query_time:.3f}ms SQL={sql}',
            'style': '{',
        },
        'database': {
            'format': '{levelname} {asctime} database POOL_STATS={pool_stats}',
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
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        'database_file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'database.log',
            'formatter': 'database',
        },
        'performance_file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'performance.log',
            'formatter': 'performance',
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
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'database': {
            'handlers': ['database_file'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'database.connection': {
            'handlers': ['database_file'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'database.performance': {
            'handlers': ['performance_file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# Asegurar que el directorio de logs exista
os.makedirs(BASE_DIR / 'logs', exist_ok=True)