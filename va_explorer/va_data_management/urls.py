from django.urls import path

from . import views

app_name = "data_management"

urlpatterns = [
    path("", view=views.Index.as_view(), name="index"),
    path("show/<int:id>", view=views.Show.as_view(), name="show"),
    path("edit/<int:id>", view=views.Edit.as_view(), name="edit"),
    path("reset/<int:id>", view=views.Reset.as_view(), name="reset"),
    path(
        "revert_latest/<int:id>",
        view=views.RevertLatest.as_view(),
        name="revert_latest",
    ),
    path(
        "run_coding_algorithms",
        view=views.RunCodingAlgorithm.as_view(),
        name="run_coding_algorithms",
    ),
]
