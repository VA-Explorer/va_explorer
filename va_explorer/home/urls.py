from django.urls import path

from . import views

app_name = "home"

urlpatterns = [
    path("", view=views.index, name="index"),
    path("about/", view=views.about, name="about"),
]
