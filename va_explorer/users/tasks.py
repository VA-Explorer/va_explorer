from django.contrib.auth import get_user_model

from config.celery_app import app

User = get_user_model()

@celery_app.task()
def get_users_count():
    """A pointless Celery task to demonstrate usage."""
    return User.objects.count()
