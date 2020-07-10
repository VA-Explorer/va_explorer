from django.urls import path

from va_explorer.users.views import (
    user_create_view,
    user_detail_view,
    user_index_view,
    user_redirect_view,
    user_update_view,
)

app_name = "users"
urlpatterns = [
    path("~redirect/", view=user_redirect_view, name="redirect"),
    path("update/<int:pk>/", view=user_update_view, name="update"),
    path("create/", view=user_create_view, name="create"),
    path("", view=user_index_view, name="index"),
    path("<int:pk>/", view=user_detail_view, name="detail"),
]
