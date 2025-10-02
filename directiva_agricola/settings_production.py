"""
Configuración de producción para AWS App Runner
"""
import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-tsz5hz_lzl*bjf#h0ypkdcob7@friwk_x&)vebox9d%+1yu^i#')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

ALLOWED_HOSTS = ['*']  # App Runner maneja el dominio automáticamente

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    'storages',  # Para S3
    'core',
    'administracion',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Para archivos estáticos
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'core.middleware.EmpresaDbMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'core.middleware.NoCacheMiddleware',
    'core.middleware.StaticFilesNoCacheMiddleware',
]

ROOT_URLCONF = 'directiva_agricola.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'directiva_agricola.wsgi.application'

# Database configuration for RDS PostgreSQL
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('RDS_DB_NAME', 'directiva_agricola'),
        'USER': os.environ.get('RDS_USERNAME', 'postgres'),
        'PASSWORD': os.environ.get('RDS_PASSWORD', 'Directiva2024!'),
        'HOST': os.environ.get('RDS_HOSTNAME', 'localhost'),
        'PORT': os.environ.get('RDS_PORT', '5432'),
        'ATOMIC_REQUESTS': True,
        'TIME_ZONE': 'America/Mexico_City',
        'OPTIONS': {},
        'CONN_MAX_AGE': 0,
        'AUTOCOMMIT': True,
        'CONN_HEALTH_CHECKS': False,
        'TEST': {
            'CHARSET': None,
            'COLLATION': None,
            'MIGRATE': True,
            'MIRROR': None,
            'NAME': None
        },
    },
    'administracion': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('RDS_ADMIN_DB_NAME', 'directiva_administracion'),
        'USER': os.environ.get('RDS_USERNAME', 'postgres'),
        'PASSWORD': os.environ.get('RDS_PASSWORD', 'Directiva2024!'),
        'HOST': os.environ.get('RDS_HOSTNAME', 'localhost'),
        'PORT': os.environ.get('RDS_PORT', '5432'),
        'ATOMIC_REQUESTS': True,
        'TIME_ZONE': 'America/Mexico_City',
        'OPTIONS': {},
        'CONN_MAX_AGE': 0,
        'AUTOCOMMIT': True,
        'CONN_HEALTH_CHECKS': False,
        'TEST': {
            'CHARSET': None,
            'COLLATION': None,
            'MIGRATE': True,
            'MIRROR': None,
            'NAME': None
        },
    }
}

# Router para bases de datos
DATABASE_ROUTERS = ['directiva_agricola.db_router.EmpresaRouter']

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

# Static files configuration for S3
AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
AWS_STORAGE_BUCKET_NAME = os.environ.get('AWS_STORAGE_BUCKET_NAME')
AWS_S3_REGION_NAME = os.environ.get('AWS_S3_REGION_NAME', 'us-west-2')
AWS_S3_CUSTOM_DOMAIN = f'{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com'
AWS_DEFAULT_ACL = 'public-read'
AWS_S3_OBJECT_PARAMETERS = {
    'CacheControl': 'max-age=86400',
}

# Static files
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
STATIC_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/static/'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

# Media files
DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
MEDIA_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Configuración de autenticación personalizada
AUTH_USER_MODEL = 'core.Usuario'

# Configuración de sesiones
SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_COOKIE_AGE = 1209600  # 2 semanas
SESSION_COOKIE_NAME = 'sessionid'
SESSION_COOKIE_SECURE = True  # HTTPS en producción
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
SESSION_SAVE_EVERY_REQUEST = False
SESSION_EXPIRE_AT_BROWSER_CLOSE = False
SESSION_SERIALIZER = 'django.contrib.sessions.serializers.JSONSerializer'

# Configuración de login/logout
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/login/'

# Configuración de cache
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
        'TIMEOUT': 300,  # 5 minutos
        'OPTIONS': {
            'MAX_ENTRIES': 1000,
        }
    }
}

# Headers de cache
CACHE_MIDDLEWARE_SECONDS = 0
CACHE_MIDDLEWARE_KEY_PREFIX = 'directiva_agricola'

# Configuración CSRF
CSRF_COOKIE_AGE = 31449600  # 1 año
CSRF_COOKIE_DOMAIN = None
CSRF_COOKIE_HTTPONLY = False
CSRF_COOKIE_NAME = 'csrftoken'
CSRF_COOKIE_PATH = '/'
CSRF_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_SECURE = True  # HTTPS en producción
CSRF_USE_SESSIONS = False

# Security settings
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_HSTS_SECONDS = 31536000  # 1 año
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True