""" my_module.py
    cannot figure out why isort is complaining about line 12

   isort:skip_file
"""
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse, reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic import (
    CreateView,
    DetailView,
    ListView,
    RedirectView,
    UpdateView,
)

from .forms import ExtendedUserCreationForm

User = get_user_model()


class UserIndexView(LoginRequiredMixin, ListView):
    login_url = reverse_lazy("users:login")
    model = User


user_index_view = UserIndexView.as_view()


class UserCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    login_url = reverse_lazy("users:login")
    form_class = ExtendedUserCreationForm
    template_name = "users/user_create.html"
    success_message = "User successfully created!"

    def form_valid(self, form):
        user = form.save(commit=False)
        user.save()

        return super(UserCreateView, self).form_valid(form)


user_create_view = UserCreateView.as_view()


class UserDetailView(LoginRequiredMixin, DetailView):
    model = User


user_detail_view = UserDetailView.as_view()


class UserUpdateView(LoginRequiredMixin, UpdateView):

    model = User
    fields = ["first_name", "last_name", "email", "is_superuser"]

    def get_success_url(self):
        return reverse("users:detail", kwargs={"pk": self.kwargs["pk"]})

    def get_object(self):
        return User.objects.get(pk=self.kwargs["pk"])

    def form_valid(self, form):
        messages.add_message(
            self.request, messages.INFO, _("User successfully updated!")
        )
        return super().form_valid(form)


user_update_view = UserUpdateView.as_view()


class UserRedirectView(LoginRequiredMixin, RedirectView):
    permanent = False

    def get_redirect_url(self):
        return reverse("users:detail", kwargs={"pk": self.request.user.id})


user_redirect_view = UserRedirectView.as_view()
