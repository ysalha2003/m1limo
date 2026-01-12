# config/settings.py
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
BASE_DIR = Path(__file__).resolve().parent

# --- Core Settings ---
SECRET_KEY = os.environ.get('SECRET_KEY', '+fn=KT]7p&XGz5BWqdXcdi8whEZK66Nl#-?G&pzEU{(LW~z6,F')
DEBUG = os.environ.get('DEBUG', 'True').lower() == 'true'

ALLOWED_HOSTS = ['62.169.19.39', 'localhost', '127.0.0.1', 'm1limo.com']

# --- CRITICAL FIX FOR 403 ERROR ---
# This tells Django to trust requests coming from this specific IP and Port
CSRF_TRUSTED_ORIGINS = ['http://62.169.19.39:8081']

# Force custom error pages even in DEBUG mode (for testing custom 404/500 pages)
FORCE_CUSTOM_ERROR_PAGES = os.environ.get('FORCE_CUSTOM_ERROR_PAGES', 'True').lower() == 'true'

# --- Application Definitions ---
DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
]

THIRD_PARTY_APPS = [
    'background_task',  # Async task queue for email sending
]

LOCAL_APPS = [
    'apps.BookingsConfig',
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'middleware.RateLimitMiddleware',  # Rate limiting for booking forms
    'middleware_custom_errors.ForceCustomErrorPagesMiddleware',  # Force custom error pages in DEBUG mode
]

ROOT_URLCONF = 'urls'

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
                'context_processors.recent_activity',  # Add recent booking activity to navbar
            ],
            'libraries': {
                'booking_filters': 'templatetags.booking_filters',
            },
        },
    },
]

WSGI_APPLICATION = 'wsgi.application'

# --- Database Configuration ---
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# --- Password Validation ---
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# --- Internationalization & Localization ---
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'America/Chicago'
USE_I18N = True
USE_TZ = True
USE_L10N = True

# --- Static & Media Files ---
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# --- Authentication ---
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_REDIRECT_URL = '/'

# =============================================================================
# CACHING CONFIGURATION
# =============================================================================
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'm1limo-cache',
        'TIMEOUT': 300,
        'OPTIONS': {
            'MAX_ENTRIES': 1000,
        }
    }
}

# Session settings
SESSION_ENGINE = 'django.contrib.sessions.backends.cached_db'
SESSION_COOKIE_AGE = 1209600  # 2 weeks
SESSION_SAVE_EVERY_REQUEST = False  # Only save when session is modified

# =============================================================================
# EMAIL CONFIGURATION
# =============================================================================
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'mail.m1limo.com')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', '465'))
EMAIL_USE_SSL = os.environ.get('EMAIL_USE_SSL', 'True').lower() == 'true'
EMAIL_USE_TLS = False  # Using SSL on port 465, not TLS
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', 'reservations@m1limo.com')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', 'Zak2020$')
EMAIL_TIMEOUT = 5

DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'M1 Limousine <reservations@m1limo.com>')
SERVER_EMAIL = os.environ.get('SERVER_EMAIL', 'reservations@m1limo.com')
ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL', 'mo@m1limo.com')

ADMINS = [
    ('Admin', ADMIN_EMAIL),
]

# =============================================================================
# APPLICATION SETTINGS
# =============================================================================
ITEMS_PER_PAGE = 10

COMPANY_INFO = {
    'name': 'M1 Limousine',
    'phone': '+1 (630) 504-8820',
    'email': 'mo@m1limo.com',
    'address': '405 Walters Lane, Suite #2B Itasca, IL 60143',
    'website': 'https://www.m1limo.com',
    'logo_url': '/static/images/logo-white.png',
}

# =============================================================================
# LOGGING CONFIGURATION
# =============================================================================
(BASE_DIR / 'logs').mkdir(exist_ok=True)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs' / 'm1limo.log',
            'formatter': 'verbose',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 10,
        },
    },
    'loggers': {
        'bookings': {
            'handlers': ['console', 'file'] if DEBUG else ['file'],
            'level': 'INFO',
            'propagate': True,
        },
        'services': {
            'handlers': ['console', 'file'] if DEBUG else ['file'],
            'level': 'INFO',
            'propagate': True,
        },
        'django.request': {
            'handlers': ['console', 'file'],
            'level': 'ERROR',
            'propagate': False,
        },
    },
    'root': {
        'handlers': ['console', 'file'] if DEBUG else ['file'],
        'level': 'INFO',
    },
}

# Security settings for production
if not DEBUG:
    SECURE_HSTS_SECONDS = 518400
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    # SSL/Secure Cookies Disabled for Port 8081 Access
    SECURE_SSL_REDIRECT = False
    SESSION_COOKIE_SECURE = False
    CSRF_COOKIE_SECURE = False
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'
