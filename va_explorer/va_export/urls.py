from django.urls import path

from va_explorer.va_export.views import download_view, va_api_view

app_name = "va_export"
urlpatterns = [
    path("verbalautopsy/", view=va_api_view, name="va_api"),
    path("", view=download_view, name="download_form"),
]
