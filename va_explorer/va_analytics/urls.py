from django.urls import path

# You need to import this, even though we don't use the import here
from va_explorer.va_analytics.dash_apps import va_dashboard # noqa: F401
from va_explorer.va_analytics.views import dashboard_view, user_supervision_view

app_name = "va_analytics"
urlpatterns = [
    path("dashboard/", view=dashboard_view, name="dashboard"),
    path("supervision/", view=user_supervision_view, name="supervision"),
]
