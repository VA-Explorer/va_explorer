from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path
from django.views import defaults as default_views

urlpatterns = [
    path("", include("va_explorer.home.urls")),
    # User management
    path("users/", include("va_explorer.users.urls", namespace="users")),
    # Allauth
    path(
        "accounts/email/",
        default_views.page_not_found,
        kwargs={"exception": Exception("Page not Found")},
    ),
    path("accounts/", include("allauth.urls")),
    # Your stuff: custom urls includes go here
    path(
        "va_analytics/",
        include("va_explorer.va_analytics.urls", namespace="va_analytics"),
    ),
    path(
        "va_data_management/",
        include("va_explorer.va_data_management.urls", namespace="va_data_management"),
    ),
    # TODO: remove this and move DHIS functionality into export
    path("dhis/", include("va_explorer.dhis_manager.urls", namespace="dhis_manager")),
    path("va_export/", include("va_explorer.va_export.urls", namespace="va_export")),
    path(
        "va_data_cleanup/",
        include("va_explorer.va_data_cleanup.urls", namespace="va_data_cleanup"),
    ),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


if settings.DEBUG:
    # This allows the error pages to be debugged during development, just visit
    # these url in browser to see how these error pages look like.
    urlpatterns += [
        path(
            "400/",
            default_views.bad_request,
            kwargs={"exception": Exception("Bad Request!")},
        ),
        path(
            "403/",
            default_views.permission_denied,
            kwargs={"exception": Exception("Permission Denied")},
        ),
        path(
            "404/",
            default_views.page_not_found,
            kwargs={"exception": Exception("Page not Found")},
        ),
        path("500/", default_views.server_error),
    ]
    if "debug_toolbar" in settings.INSTALLED_APPS:
        import debug_toolbar

        urlpatterns = [path("__debug__/", include(debug_toolbar.urls)), *urlpatterns]
