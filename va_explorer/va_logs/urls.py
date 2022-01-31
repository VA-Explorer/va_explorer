from django.urls import path

from . import views

app_name = "va_logs"
urlpatterns = [
    path("submit_log", view=views.SubmitLog.as_view(), name="submit_log")
]
