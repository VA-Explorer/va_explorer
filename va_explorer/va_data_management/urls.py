from django.urls import path

from . import views

app_name = "data_management"

urlpatterns = [
    path("", view=views.index, name="index")
]
