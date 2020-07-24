from django.contrib import messages
from django.contrib.auth.mixins import AccessMixin
from django.http.response import HttpResponseRedirect
from django.urls import reverse


class CustomAuthMixin(AccessMixin):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            print("HIT AUTHENTICATION!!!!!!!")
            messages.error(request, "You must be signed in to view this page.")
            return self.handle_no_permission()
        elif not self.user_has_valid_password(request):
            print("HIT NO PASSWORD!!!!!!!")
            messages.error(
                request, "You must set a new password before you can view this page."
            )
            return HttpResponseRedirect(reverse("users:set_password"))
        return super(CustomAuthMixin, self).dispatch(request, *args, **kwargs)

    def user_has_valid_password(self, request):
        return request.user.has_valid_password
