from django.contrib import messages
from django.contrib.auth.mixins import AccessMixin, UserPassesTestMixin
from django.http.response import HttpResponseRedirect
from django.urls import reverse


class CustomAuthMixin(AccessMixin):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, "You must be signed in to view this page.")
            return self.handle_no_permission()
        elif not self.user_has_valid_password(request):
            messages.error(
                request, "You must set a new password before you can view this page."
            )
            return HttpResponseRedirect(reverse("users:set_password"))
        return super().dispatch(request, *args, **kwargs)

    def user_has_valid_password(self, request):
        return request.user.has_valid_password


class UserDetailViewMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.has_perm(
            "users.view_user"
        ) or self.request.user.pk == self.kwargs.get("pk")
