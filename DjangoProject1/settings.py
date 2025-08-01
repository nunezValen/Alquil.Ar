"""
Django settings for DjangoProject1 project.

Generated by 'django-admin startproject' using Django 5.2.1.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/5.2/ref/settings/
"""

from pathlib import Path
from pyngrok import ngrok, conf

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-c_&j0lq^_c0)hv5%n_rm1y)$+%us1m@2j!j1!1g8e)2^=(3qez'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['localhost', '127.0.0.1', '.ngrok.io', '.ngrok-free.app']


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'persona',
    'widget_tweaks',
    'maquinas',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'persona.middleware.RequestMiddleware',
]

# Configuración de mensajes
MESSAGE_STORAGE = 'django.contrib.messages.storage.session.SessionStorage'

from django.contrib.messages import constants as message_constants
MESSAGE_TAGS = {
    message_constants.DEBUG: 'debug',
    message_constants.INFO: 'info',
    message_constants.SUCCESS: 'success',
    message_constants.WARNING: 'warning',
    message_constants.ERROR: 'danger',
}

# Configuración de sesiones
SESSION_EXPIRE_AT_BROWSER_CLOSE = True  # La sesión expira al cerrar el navegador
SESSION_COOKIE_AGE = 43200  # 12 horas en segundos
SESSION_SAVE_EVERY_REQUEST = True  # Actualiza la cookie de sesión en cada request

ROOT_URLCONF = 'DjangoProject1.urls'

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
                'persona.views.empleados_processor',
            ],
        },
    },
]

WSGI_APPLICATION = 'DjangoProject1.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = 'static/'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Configuración de archivos multimedia
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Configuración de CSRF y sesiones
CSRF_TRUSTED_ORIGINS = [
    'https://nearby-cat-mildly.ngrok-free.app',
    'http://localhost:8000',
    'http://127.0.0.1:8000',
    'https://*.ngrok-free.app'
]
CSRF_COOKIE_SECURE = False
SESSION_COOKIE_SECURE = False

# Configuración de login
LOGIN_URL = 'persona:login_unificado2'
LOGIN_REDIRECT_URL = '/persona/catalogo/'
LOGOUT_REDIRECT_URL = '/persona/login/'

# Configuración de APIs de pago - CLIENTES (API anterior)
MERCADOPAGO_PUBLIC_KEY = 'APP_USR-0d51d16a-0802-4957-8758-114b32d47833'
MERCADOPAGO_ACCESS_TOKEN = 'APP_USR-7174436737227422-060512-552e39d627a22667a39fc18846c5db92-2462897485'
MERCADOPAGO_CLIENT_ID = '7174436737227422'
MERCADOPAGO_CLIENT_SECRET = 'Po0AeZi9s1eI8DE7ud64kyybJMGAnCIH'

# Configuración de APIs de pago - EMPLEADOS (QR dinámico)
MERCADOPAGO_EMPLOYEE_PUBLIC_KEY = 'APP_USR-47ecf0d1-d770-4b06-abd7-80d7791b1d3e'
MERCADOPAGO_EMPLOYEE_ACCESS_TOKEN = 'APP_USR-4038683271671225-062818-74dcfb1091febaf7c51669aea383988c-343205143'
MERCADOPAGO_EMPLOYEE_CLIENT_ID = '4038683271671225'
MERCADOPAGO_EMPLOYEE_CLIENT_SECRET = 'qko7MYyxDhNnfPrLGdyuOVmbXlIlFzEW'
BINANCE_API_KEY = 'TU_API_KEY'
BINANCE_API_SECRET = 'TU_API_SECRET'

# Configuración de correo electrónico
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'contacto.alquilar@gmail.com'
EMAIL_HOST_PASSWORD = 'ulwc rybt birv dqfg'
DEFAULT_FROM_EMAIL = 'Alquil.ar <no-reply@alquilar.com.ar>'

# Configuración de ngrok
NGROK_URL = 'https://nearby-cat-mildly.ngrok-free.app'
NGROK_PORT = 8000

# Configuración automática de ngrok COMPLETAMENTE DESHABILITADA
# Usamos ngrok manual con: ngrok http 8000 --domain=nearby-cat-mildly.ngrok-free.app

# Agregamos manualmente la URL de ngrok
ALLOWED_HOSTS.append('nearby-cat-mildly.ngrok-free.app')

# Configuración para que Django sepa que está detrás de un proxy HTTPS
USE_TZ = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT = False  # ngrok ya maneja el HTTPS
