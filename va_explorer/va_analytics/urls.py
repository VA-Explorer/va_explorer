from django.urls import path

from va_explorer.va_analytics.views import (
    DashboardAPIView,
    dashboard_view,
    user_supervision_view,
)

app_name = "va_analytics"
urlpatterns = [
    path("dashboard/", view=dashboard_view, name="dashboard"),
    path("api/dashboard", view=DashboardAPIView.as_view(), name="dashboard-api"),
    path("supervision/", view=user_supervision_view, name="supervision"),
]
