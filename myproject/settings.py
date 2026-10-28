"""Django settings for myproject project (DevHelp AI).

Configured for:
- Local development with SQLite
- Optional PostgreSQL deployment via DATABASE_URL
- MongoDB persistence configuration via MONGODB_URI
- Google GenAI SDK configuration via GEMINI_API_KEY
- Production static files serving via WhiteNoise
- Custom request logging middleware
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / '.env')


# Quick-start development settings - unsuitable for production
# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-t5ht=v1zb8t4jktf@d*52p@wigtoix!&1*o%t&bqz^igwk5_pp')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get('DEBUG', 'True').lower() in ('true', '1', 'yes')

# ALLOWED_HOSTS - Supports local dev, custom domain, and Vercel domains (.vercel.app)
allowed_hosts_env = os.environ.get('ALLOWED_HOSTS', '').strip()
if allowed_hosts_env:
    ALLOWED_HOSTS = [h.strip() for h in allowed_hosts_env.split(',') if h.strip()]
    if '.vercel.app' not in ALLOWED_HOSTS:
        ALLOWED_HOSTS.append('.vercel.app')
else:
    ALLOWED_HOSTS = ['127.0.0.1', 'localhost', '.vercel.app', 'taskflow-omega-ruddy-39.vercel.app']

# CSRF Trusted Origins - Required for POST forms on HTTPS domains (e.g. *.vercel.app)
csrf_trusted_env = os.environ.get('CSRF_TRUSTED_ORIGINS', '').strip()
if csrf_trusted_env:
    CSRF_TRUSTED_ORIGINS = [o.strip() for o in csrf_trusted_env.split(',') if o.strip()]
    if 'https://*.vercel.app' not in CSRF_TRUSTED_ORIGINS:
        CSRF_TRUSTED_ORIGINS.append('https://*.vercel.app')
    if 'https://taskflow-omega-ruddy-39.vercel.app' not in CSRF_TRUSTED_ORIGINS:
        CSRF_TRUSTED_ORIGINS.append('https://taskflow-omega-ruddy-39.vercel.app')
else:
    CSRF_TRUSTED_ORIGINS = [
        'https://*.vercel.app',
        'https://taskflow-omega-ruddy-39.vercel.app',
        'http://localhost',
        'http://127.0.0.1',
    ]

# External Integrations Configuration
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '').strip()
MONGODB_URI = os.environ.get('MONGODB_URI', '').strip()


# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'myapp',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'myapp.middleware.RequestLoggingMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'myproject.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'myapp' / 'templates'],
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

WSGI_APPLICATION = 'myproject.wsgi.application'


# Database
# Supports SQLite by default and for automated test isolation; seamlessly switches to PostgreSQL if DATABASE_URL is provided in deployment.
DATABASE_URL = os.environ.get('DATABASE_URL', '').strip()
IS_TESTING = 'test' in sys.argv

if DATABASE_URL.startswith(('postgres://', 'postgresql://', 'postgresql+psycopg2://')) and not IS_TESTING:
    # Extract PostgreSQL configuration safely (compatible with Neon, Supabase, Vercel Postgres, AWS RDS)
    import urllib.parse
    url = urllib.parse.urlparse(DATABASE_URL)
    db_options = {}
    query_params = urllib.parse.parse_qs(url.query)
    if 'sslmode' in query_params:
        db_options['sslmode'] = query_params['sslmode'][0]
    elif url.hostname not in ('localhost', '127.0.0.1'):
        db_options['sslmode'] = 'require'

    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': urllib.parse.unquote(url.path.lstrip('/')),
            'USER': urllib.parse.unquote(url.username or ''),
            'PASSWORD': urllib.parse.unquote(url.password or ''),
            'HOST': url.hostname,
            'PORT': url.port or 5432,
            'OPTIONS': db_options,
            'CONN_MAX_AGE': int(os.environ.get('CONN_MAX_AGE', '0')),
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
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
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True


# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# WhiteNoise production storage
STORAGES = {
    'default': {
        'BACKEND': 'django.core.files.storage.FileSystemStorage',
    },
    'staticfiles': {
        'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage',
    },
}
WHITENOISE_MANIFEST_STRICT = False

# HTTPS & Security Settings (active when SECURE_SSL_REDIRECT=True in production)
# Honor X-Forwarded-Proto for request.is_secure() behind reverse proxies like Vercel
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT = os.environ.get('SECURE_SSL_REDIRECT', 'False').lower() in ('true', '1', 'yes')
SESSION_COOKIE_SECURE = os.environ.get('SESSION_COOKIE_SECURE', 'False').lower() in ('true', '1', 'yes')
CSRF_COOKIE_SECURE = os.environ.get('CSRF_COOKIE_SECURE', 'False').lower() in ('true', '1', 'yes')
SECURE_HSTS_SECONDS = int(os.environ.get('SECURE_HSTS_SECONDS', '0'))


# Logging Configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '[%(asctime)s] %(levelname)s [%(name)s]: %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'standard',
        },
    },
    'loggers': {
        'devhelp': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': True,
        },
        'django.request': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
    },
}
