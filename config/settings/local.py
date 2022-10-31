from .base import *  # noqa
from .base import env

# General

DEBUG = env.bool("DJANGO_DEBUG", True)

SECRET_KEY = env(
    "DJANGO_SECRET_KEY",
    default="5f3L19XwGlfzvyaHwWjtYDvQbFFM3qjzsWwbUI1XddPysCQGN1kv4y7RWY6TqWum",
)

ALLOWED_HOSTS = ["localhost", "0.0.0.0", "127.0.0.1"]

CORS_ALLOWED_ORIGINS = ["http://localhost:8080"]

INTERNAL_IPS = ["127.0.0.1", "10.0.2.2"]

# Celery

CELERY_TASK_EAGER_PROPAGATES = True
