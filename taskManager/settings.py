# Django settings - hardened against findings in report.txt
# Fixes:
#   B105 SECRET_KEY moved to env (CWE-259)
#   Cookie HttpOnly/SameSite/Secure flags (CWE-1004 / CWE-1275)
#   Security headers via SecurityMiddleware + django-csp (CWE-693)
#   PBKDF2 replaces MD5PasswordHasher (CWE-916)
#   Server-side sessions (signed_cookies + Pickle was unsafe)
import os
from pathlib import Path

from decouple import Csv, config

BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY: SECRET_KEY pulled from environment - never commit secrets
SECRET_KEY = config(
    'SECRET_KEY',
    default='dev-only-insecure-key-change-me-via-env',
)

# SECURITY: DEBUG defaults False; opt in via env for development
DEBUG = config('DEBUG', default=False, cast=bool)

ALLOWED_HOSTS = config(
    'ALLOWED_HOSTS',
    default='127.0.0.1,localhost',
    cast=Csv(),
)

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    # SECURITY: WhiteNoise serves static files through MIDDLEWARE so CSP
    # and other security headers apply to them too. The 'runserver_nostatic'
    # entry must come before django.contrib.staticfiles to disable the
    # dev server's middleware-bypassing static handler.
    'whitenoise.runserver_nostatic',
    'django.contrib.staticfiles',
    'csp',
    'taskManager',
]

# SECURITY: SecurityMiddleware first; WhiteNoise serves static files
# through the middleware stack so CSP/security headers apply to them too;
# CSP enabled, CSRF enforced.
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'csp.middleware.CSPMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'taskManager.urls'

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

WSGI_APPLICATION = 'taskManager.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATICFILES_DIRS = (
    [BASE_DIR / 'static'] if (BASE_DIR / 'static').exists() else []
)
STATIC_ROOT = BASE_DIR / 'staticfiles'

LOGIN_URL = '/taskManager/login/'

# SECURITY: PBKDF2 replaces MD5; MD5 left last only so legacy fixture
# accounts can log in once and be transparently upgraded by Django.
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher',
    'django.contrib.auth.hashers.Argon2PasswordHasher',
    'django.contrib.auth.hashers.BCryptSHA256PasswordHasher',
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

# SECURITY: server-side sessions (signed_cookies + PickleSerializer was unsafe)
SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Strict'
SESSION_COOKIE_SECURE = not DEBUG

CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = 'Strict'
CSRF_COOKIE_SECURE = not DEBUG

# SECURITY: response hardening (X-Content-Type-Options, HSTS, Referrer)
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_REFERRER_POLICY = 'same-origin'
X_FRAME_OPTIONS = 'DENY'
SECURE_HSTS_SECONDS = 0 if DEBUG else 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = not DEBUG
SECURE_HSTS_PRELOAD = not DEBUG
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# SECURITY: Content-Security-Policy via django-csp 4.x dict API (CWE-693).
# - 'unsafe-inline' removed from style/script (CWE-79).
# - form-action / frame-src / connect-src / manifest-src / worker-src / media-src
#   declared explicitly so ZAP "directive with no fallback" warning is satisfied.
_CSP_SELF = ("'self'",)
CONTENT_SECURITY_POLICY = {
    'DIRECTIVES': {
        'default-src':     _CSP_SELF,
        'script-src':      _CSP_SELF,
        'script-src-elem': _CSP_SELF,
        'script-src-attr': ("'none'",),
        'style-src':       _CSP_SELF,
        'style-src-elem':  _CSP_SELF,
        'style-src-attr':  ("'none'",),
        'font-src':        _CSP_SELF,
        'img-src':         ("'self'", 'data:'),
        'connect-src':     _CSP_SELF,
        'media-src':       _CSP_SELF,
        'manifest-src':    _CSP_SELF,
        'worker-src':      _CSP_SELF,
        'frame-src':       ("'none'",),
        'frame-ancestors': ("'none'",),
        'object-src':      ("'none'",),
        'base-uri':        _CSP_SELF,
        'form-action':     _CSP_SELF,
    },
}

FILE_UPLOAD_HANDLERS = (
    'django.core.files.uploadhandler.TemporaryFileUploadHandler',
)

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
EMAIL_PORT = 1025

MESSAGE_STORAGE = 'django.contrib.messages.storage.cookie.CookieStorage'
