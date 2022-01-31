from django.core.management.utils import get_random_secret_key

from .base import *  # noqa
from .base import env

# General

DEBUG = env.bool("DJANGO_DEBUG", False)

SECRET_KEY = env("DJANGO_SECRET_KEY", default=get_random_secret_key())

ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS", default=["va_explorer.org"])

# Caches

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": env("REDIS_URL", default="redis://localhost:6379/0"),
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            # Mimicing memcache behavior.
            # http://jazzband.github.io/django-redis/latest/#_memcached_exceptions_behavior
            "IGNORE_EXCEPTIONS": True,
        },
    }
}


# Static

STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# Templates

TEMPLATES[-1]["OPTIONS"]["loaders"] = [  # type: ignore[index] # noqa F405
    (
        "django.template.loaders.cached.Loader",
        [
            "django.template.loaders.filesystem.Loader",
            "django.template.loaders.app_directories.Loader",
        ],
    )
]

# Logging
LOG_DIR = env("LOG_DIR", default="/app/va_explorer/va_logs")
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {"require_debug_false": {"()": "django.utils.log.RequireDebugFalse"}},
    "formatters": {
        "verbose": {
            "format": "%(levelname)s %(asctime)s %(module)s "
            "%(process)d %(thread)d %(message)s"
        },
        "debug": {
            "format": "%(asctime)s - %(name)s [%(filename)s:%(lineno)s - %(funcName)5s()]  %(message)s"
        }, 
        "event": {
            "format": "%(asctime)s - %(message)s"
        }
    },
    "handlers": {
        "mail_admins": {
            "level": "ERROR",
            "filters": ["require_debug_false"],
            "class": "django.utils.log.AdminEmailHandler",
        },
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
        "ingest_file": {
            "level": "DEBUG",
            "class": "logging.FileHandler",
            "filename": f"{LOG_DIR}/logfiles/data_ingest.log",
            "formatter": "debug"
        },
        "event_file": {
            "level": "INFO",
            "class": "logging.FileHandler",
            "filename": f"{LOG_DIR}/logfiles/events.log",
            "formatter": "event"

        }
    },
    "root": {"level": "INFO", "handlers": ["console"]},
    "loggers": {
        "django.request": {
            "handlers": ["mail_admins"],
            "level": "ERROR",
            "propagate": True,
        },
        "django.security.DisallowedHost": {
            "level": "ERROR",
            "handlers": ["console", "mail_admins"],
            "propagate": True,
        },
        "ingest_logger": {
            "level": "DEBUG",
            "handlers": ["ingest_file"],
            "propagate": False
        },
        "event_logger": {
            "level": "INFO",
            "handlers": ["event_file"],
            "propagate": False
        }
    },
}
