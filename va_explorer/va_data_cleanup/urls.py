from django.urls import path

from . import views

app_name = "data_cleanup"

urlpatterns = [
    path("", view=views.DataCleanupIndexView.as_view(), name="index"),
    path("download/<int:pk>", view=views.DownloadIndividual.as_view(), name="download"),
    path("download_all", view=views.DownloadAll.as_view(), name="download_all"),
    path(
        "download_questions",
        view=views.DownloadQuestions.as_view(),
        name="download_questions",
    ),
]
