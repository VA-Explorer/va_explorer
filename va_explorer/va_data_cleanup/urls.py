from django.urls import path

from . import views

app_name = "va_data_cleanup"

urlpatterns = [
    path("", view=views.DataCleanupIndexView.as_view(), name="index"),
]
