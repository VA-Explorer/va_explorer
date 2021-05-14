from django.urls import path
from . import views


app_name = "logs"
urlpatterns = [
    path("", view=views.Index.as_view(), name="index"), 
    path("submit_log", view=views.SubmitLog.as_view(), name="submit_log")
    #path("index", view=logging_submission, name="logging"),
]
