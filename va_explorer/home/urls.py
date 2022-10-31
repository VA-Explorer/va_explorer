from django.urls import path

from . import views
from .views import trends_endpoint_view

app_name = "home"

urlpatterns = [
    path("", view=views.Index.as_view(), name="index"),
    path("about/", view=views.About.as_view(), name="about"),
    path("trends/", trends_endpoint_view, name="charts"),
]
