"""
Base settings to build other settings files upon.
"""

import os
from pathlib import Path

import environ

ROOT_DIR = Path(__file__).resolve(strict=True).parent.parent.parent
APPS_DIR = ROOT_DIR / "va_explorer"

env = environ.Env()
env.read_env(str(ROOT_DIR / ".env"))

# General

TIME_ZONE = "UTC"
# accepted date formats for VA records
DATE_FORMATS = {
    "%Y-%m-%d": "yyyy-mm-dd",
    "%m/%d/%Y": "mm/dd/yyyy",
    "%m/%d/%y": "mm/dd/yy",
    "%d/%m/%Y": "dd/mm/yyyy",
    "%d/%m/%y": "dd/mm/yy",
    "%Y-%m-%d %H:%M:%S": "yyyy-mm-dd HH:MM:SS",
}
LANGUAGE_CODE = "en-us"
SITE_ID = 1
USE_I18N = True
USE_TZ = True
LOCALE_PATHS = [str(ROOT_DIR / "locale")]

# App-specific Configuration

# ==> Configuration for automatic duplicates detection
# VA Explorer will automatically mark Verbal Autopsies as duplicates if
# QUESTIONS_TO_AUTODETECT_DUPLICATES is defined
# Questions must be passed as a comma-separated list, for example,
# "Id10017, Id10018, Id10019, Id10020"
# The question IDs passed into the list must match a field in the VerbalAutopsy model
# By default, automatic duplicates detection is turned off
QUESTIONS_TO_AUTODETECT_DUPLICATES = os.environ.get(
    "QUESTIONS_TO_AUTODETECT_DUPLICATES", None
)

DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

# Databases

db_user = os.environ.get("POSTGRES_USER", "postgres")
db_password = os.environ.get("POSTGRES_PASSWORD", "postgres")
db_host = os.environ.get("POSTGRES_HOST", "localhost")
db_port = os.environ.get("POSTGRES_PORT", "5432")
db_db = os.environ.get("POSTGRES_DB", "va_explorer")

DATABASES = {
    "default": env.db(
        "DATABASE_URL",
        default=f"postgres://{db_user}:{db_password}@{db_host}:{db_port}/{db_db}",
    )
}
DATABASES["default"]["ATOMIC_REQUESTS"] = True
DATABASES["default"]["CONN_MAX_AGE"] = env.int("CONN_MAX_AGE", default=60)

# URLs

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"

# Apps

DJANGO_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.sites",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # "django.contrib.humanize", # Handy template tags
    "django.forms",
]

THIRD_PARTY_APPS = [
    "rest_framework",
    "crispy_forms",
    "allauth",
    "allauth.account",
    "django_celery_beat",
    "simple_history",
    "debug_toolbar",
    "whitenoise.runserver_nostatic",
    "django_extensions",
    "bootstrap4",
    "django_filters",
    "django_pivot",
    "corsheaders",
]

LOCAL_APPS = [
    "va_explorer.home.apps.HomeConfig",
    "va_explorer.users.apps.UsersConfig",
    "va_explorer.va_analytics.apps.VaAnalyticsConfig",
    "va_explorer.va_data_management.apps.VaDataManagementConfig",
    "va_explorer.dhis_manager.apps.DhisManagerConfig",
    "va_explorer.va_export.apps.VaExportConfig",
    "va_explorer.va_data_cleanup.apps.VaDataCleanupConfig",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

# Authentication

AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
]
AUTH_USER_MODEL = "users.User"
LOGIN_REDIRECT_URL = "users:redirect"
LOGIN_URL = "account_login"
ACCOUNT_LOGOUT_REDIRECT_URL = "account_login"

# Passwords

PASSWORD_HASHERS = [
    # https://docs.djangoproject.com/en/dev/topics/auth/passwords/#using-argon2-with-django
    "django.contrib.auth.hashers.Argon2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher",
    "django.contrib.auth.hashers.BCryptSHA256PasswordHasher",
]
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
    {"NAME": "va_explorer.users.validators.PasswordComplexityValidator"},
    {"NAME": "va_explorer.users.validators.PasswordHistoryValidator"},
]

# Middleware

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.common.BrokenLinkEmailsMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    # Track which user makes VA data edits
    "simple_history.middleware.HistoryRequestMiddleware",
    "debug_toolbar.middleware.DebugToolbarMiddleware",
]

DEBUG_TOOLBAR_CONFIG = {
    "DISABLE_PANELS": ["debug_toolbar.panels.redirects.RedirectsPanel"],
    "SHOW_TEMPLATE_CONTEXT": True,
}

# Static

STATIC_ROOT = str(ROOT_DIR / "staticfiles")
STATIC_URL = "/static/"
STATICFILES_DIRS = [str(APPS_DIR / "static")]
STATICFILES_FINDERS = [
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
]

# Media

MEDIA_ROOT = str(APPS_DIR / "media")
MEDIA_URL = "/media/"

# Templates

TEMPLATES = [
    {
        # https://docs.djangoproject.com/en/dev/ref/settings/#std:setting-TEMPLATES-BACKEND
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        # https://docs.djangoproject.com/en/dev/ref/settings/#template-dirs
        "DIRS": [str(APPS_DIR / "templates")],
        "OPTIONS": {
            # https://docs.djangoproject.com/en/dev/ref/settings/#template-loaders
            # https://docs.djangoproject.com/en/dev/ref/templates/api/#loader-types
            "loaders": [
                "django.template.loaders.filesystem.Loader",
                "django.template.loaders.app_directories.Loader",
            ],
            # https://docs.djangoproject.com/en/dev/ref/settings/#template-context-processors
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.template.context_processors.i18n",
                "django.template.context_processors.media",
                "django.template.context_processors.static",
                "django.template.context_processors.tz",
                "django.contrib.messages.context_processors.messages",
                "va_explorer.utils.context_processors.settings_context",
                "va_explorer.utils.context_processors.auto_detect_duplicates",
                "va_explorer.utils.context_processors.duplicates_count",
            ],
            "libraries": {
                "va_explorer_tags": "va_explorer.templatetags.va_explorer_tags"
            },
        },
    }
]

FORM_RENDERER = "django.forms.renderers.TemplatesSetting"
CRISPY_TEMPLATE_PACK = "bootstrap4"

FIXTURE_DIRS = (str(APPS_DIR / "fixtures"),)

# Security

SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True
SECURE_BROWSER_XSS_FILTER = True
DATA_UPLOAD_MAX_MEMORY_SIZE = None

# Email

email_config = env.email_url("EMAIL_URL", default="consolemail://")
EMAIL_BACKEND = email_config["EMAIL_BACKEND"]
EMAIL_HOST_USER = email_config["EMAIL_HOST_USER"]
EMAIL_HOST_PASSWORD = email_config["EMAIL_HOST_PASSWORD"]
EMAIL_HOST = email_config["EMAIL_HOST"]
EMAIL_PORT = email_config["EMAIL_PORT"]
EMAIL_FILE_PATH = email_config["EMAIL_FILE_PATH"]
EMAIL_TIMEOUT = 5

DEFAULT_FROM_EMAIL = env(
    "DJANGO_DEFAULT_FROM_EMAIL", default="VA Explorer <noreply@vaexplorer.org>"
)
SERVER_EMAIL = env("DJANGO_SERVER_EMAIL", default=DEFAULT_FROM_EMAIL)
EMAIL_SUBJECT_PREFIX = env("DJANGO_EMAIL_SUBJECT_PREFIX", default="[VA Explorer] ")

# Logging
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "%(levelname)s %(asctime)s %(module)s "
            "%(process)d %(thread)d %(message)s"
        },
        "debug": {
            "format": "%(asctime)s - %(name)s "
            "[%(filename)s:%(lineno)s - %(funcName)5s()]  %(message)s"
        },
    },
    "handlers": {
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "root": {"level": "INFO", "handlers": ["console"]},
}

# Caches

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "",
    }
}

# Celery
if USE_TZ:
    CELERY_TIMEZONE = TIME_ZONE
CELERY_BROKER_URL = env("CELERY_BROKER_URL", default="redis://redis:6379/0")
CELERY_RESULT_BACKEND = CELERY_BROKER_URL
CELERY_RESULT_EXTENDED = True
CELERY_RESULT_BACKEND_ALWAYS_RETRY = True
CELERY_RESULT_BACKEND_MAX_RETRIES = 5
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"

# 2700 = 45min before worker task exception + potential cleanup
# 3000 = 50min before forced termination of worker task
# Needed for long-running import & coding jobs
CELERY_TASK_TIME_LIMIT = 3000
CELERY_TASK_SOFT_TIME_LIMIT = 2700

CELERY_BEAT_SCHEDULER = "django_celery_beat.schedulers:DatabaseScheduler"
CELERY_WORKER_SEND_TASK_EVENTS = True
CELERY_TASK_SEND_SENT_EVENT = True

# Allauth
ACCOUNT_ALLOW_REGISTRATION = env.bool("DJANGO_ACCOUNT_ALLOW_REGISTRATION", False)
ACCOUNT_AUTHENTICATION_METHOD = "email"
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_EMAIL_VERIFICATION = "none"
ACCOUNT_ADAPTER = "va_explorer.users.adapters.AccountAdapter"
ACCOUNT_USER_MODEL_USERNAME_FIELD = None
ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_USER_DISPLAY = lambda user: user.name  # noqa: E731 - allow this limited use
