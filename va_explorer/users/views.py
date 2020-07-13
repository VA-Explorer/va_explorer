""" my_module.py
    cannot figure out why isort is complaining about line 12

   isort:skip_file
"""
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse, reverse_lazy
from django.views.generic import (
    CreateView,
    DetailView,
    ListView,
    RedirectView,
    UpdateView,
)


from .forms import ExtendedUserCreationForm

User = get_user_model()


class UserIndexView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    # https://github.com/pennersr/django-allauth/blob/c19a212c6ee786af1bb8bc1b07eb2aa8e2bf531b/allauth/account/urls.py
    login_url = reverse_lazy("account_login")
    model = User

    # NOTE: This is a dummy test to understand the UserPassesTestMixin
    def test_func(self):
        return self.request.user.email.endswith("@example.com")


user_index_view = UserIndexView.as_view()


class UserCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    login_url = reverse_lazy("account_login")
    form_class = ExtendedUserCreationForm
    template_name = "users/user_create.html"
    success_message = "User successfully created!"

    def get_form_kwargs(self):
        kw = super(UserCreateView, self).get_form_kwargs()
        kw["request"] = self.request  # the trick!
        return kw

    def form_valid(self, form):
        return super().form_valid(form)


user_create_view = UserCreateView.as_view()


class UserDetailView(LoginRequiredMixin, DetailView):
    login_url = reverse_lazy("account_login")
    model = User


user_detail_view = UserDetailView.as_view()


class UserUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    login_url = reverse_lazy("account_login")
    model = User
    fields = ["first_name", "last_name", "email", "is_superuser"]
    success_message = "User successfully updated!"

    def get_success_url(self):
        return reverse("users:detail", kwargs={"pk": self.kwargs["pk"]})

    def get_object(self):
        return User.objects.get(pk=self.kwargs["pk"])

    def form_valid(self, form):
        return super().form_valid(form)


user_update_view = UserUpdateView.as_view()


class UserRedirectView(LoginRequiredMixin, RedirectView):
    login_url = reverse_lazy("account_login")
    permanent = False

    def get_redirect_url(self):
        return reverse("users:detail", kwargs={"pk": self.request.user.id})


user_redirect_view = UserRedirectView.as_view()
