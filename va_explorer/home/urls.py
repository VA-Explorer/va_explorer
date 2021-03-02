from django.urls import path

from . import views

app_name = "home"

urlpatterns = [
    path("", view=views.Index.as_view(), name="index"),
    path("about/", view=views.About.as_view(), name="about"),
]
