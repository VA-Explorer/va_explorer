from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class UsersConfig(AppConfig):
    name = "va_explorer.users"
    verbose_name = _("Users")

    def ready(self):
        try:
            import va_explorer.users.signals  # noqa F401
        except ImportError:
            pass
