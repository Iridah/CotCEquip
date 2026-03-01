import os
from pathlib import Path
import environ

# BASE_DIR es /home/vstore/Programacion/CotCEquip/CotcEquip
BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env(
    DEBUG=(bool, False),
    DB_PORT=(int, 5432)
)

# Buscamos el .env específicamente en la raíz del repositorio o en la raíz de la app
# Probamos las dos rutas más probables según tu descripción
possible_env_paths = [
    os.path.join(BASE_DIR, '.env'),          # ~/Programacion/CotCEquip/CotcEquip/.env
    os.path.join(BASE_DIR.parent, '.env')   # ~/Programacion/CotCEquip/.env
]

env_loaded = False
for path in possible_env_paths:
    if os.path.exists(path):
        environ.Env.read_env(path)
        env_loaded = True
        break

# Si esto falla ahora, te dirá exactamente qué intentó
if not env_loaded:
    print(f" CRITICAL: No se encontró el archivo .env en: {possible_env_paths}")

SECRET_KEY = env('SECRET_KEY')
DEBUG = env('DEBUG')
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=['127.0.0.1', 'localhost'])

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Third party
    'rest_framework',
    'corsheaders',
    # Local
    'api',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware', # Debe ir arriba
    'django.middleware.common.CommonMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'CotcEquip.urls'

# Configuración de Postgres (Tal cual la pediste)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': env('DB_NAME'),
        'USER': env('DB_USER'),
        'PASSWORD': env('DB_PASSWORD'),
        'HOST': env('DB_HOST'),
        'PORT': env('DB_PORT'),
        'OPTIONS': {
            'options': '-c search_path=public'
        },
    }
}

# CORS
CORS_ALLOW_ALL_ORIGINS = True # Ajustar en producción

# Configuración de DRF (opcional pero recomendada)
REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 100
}

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'api' / 'templates'],
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

WSGI_APPLICATION = 'CotcEquip.wsgi.application'

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'es-cl'
TIME_ZONE = 'America/Santiago'
USE_I18N = True
USE_TZ = True

# Estáticos
STATIC_URL = 'static/'
STATICFILES_DIRS = [
    os.path.join(BASE_DIR.parent, 'static'),
]
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Media
MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'data/raw_images'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'