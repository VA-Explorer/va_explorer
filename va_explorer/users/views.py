from django.contrib.auth import get_user_model, update_session_auth_hash
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse, reverse_lazy
from django.views.generic import (
    CreateView,
    DetailView,
    FormView,
    ListView,
    RedirectView,
    UpdateView,
)

from ..utils.mixins import CustomAuthMixin
from .forms import ExtendedUserCreationForm, UserSetPasswordForm, UserUpdateForm

User = get_user_model()


class UserIndexView(CustomAuthMixin, PermissionRequiredMixin, ListView):
    # https://github.com/pennersr/django-allauth/blob/c19a212c6ee786af1bb8bc1b07eb2aa8e2bf531b/allauth/account/urls.py
    login_url = reverse_lazy("account_login")
    permission_required = "users.view_user"
    model = User
    paginate_by = 10
    queryset = User.objects.all().order_by("name")


user_index_view = UserIndexView.as_view()


class UserCreateView(
    CustomAuthMixin, PermissionRequiredMixin, SuccessMessageMixin, CreateView
):
    login_url = reverse_lazy("account_login")
    permission_required = "users.add_user"
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


class UserDetailView(CustomAuthMixin, PermissionRequiredMixin, DetailView):
    login_url = reverse_lazy("account_login")
    permission_required = "users.view_user"
    model = User


user_detail_view = UserDetailView.as_view()


class UserUpdateView(
    CustomAuthMixin, PermissionRequiredMixin, SuccessMessageMixin, UpdateView
):
    login_url = reverse_lazy("account_login")
    permission_required = "users.change_user"
    form_class = UserUpdateForm
    template_name = "users/user_update.html"
    success_message = "User successfully updated!"

    def get_success_url(self):
        return reverse("users:detail", kwargs={"pk": self.kwargs["pk"]})

    def get_object(self):
        return User.objects.get(pk=self.kwargs["pk"])

    def form_valid(self, form):
        return super().form_valid(form)

    def get_initial(self):
        """
        Initializes the user's group on the form, which in our case is not done by default even
        though we are using a model-bound form. (Note that Group is a model from django.contrib.auth
        that is m2m with User.) We want to permit a user to be assigned to one Group only and thus must
        manually initialize the UpdateForm since we are imposing a change on the relation through how we
        allow the user to be assigned to groups.

        Initializes the form display to show whether the user has national or location-specific
        geographic access. If there are any locations associated with the user in the database,
        they have location-specific access; else national access.
        """
        initial = super(UserUpdateView, self).get_initial()
        initial["group"] = self.get_object().groups.first()
        initial["geographic_access"] = (
            "location-specific" if self.get_object().locations.exists() else "national"
        )
        return initial

    # TODO: Remove if we do not require email confirmation; we will no longer need the lines below
    # def get_form_kwargs(self):
    #     kw = super(UserUpdateView, self).get_form_kwargs()
    #     kw["request"] = self.request  # the trick!
    #     return kw


user_update_view = UserUpdateView.as_view()


class UserRedirectView(LoginRequiredMixin, RedirectView):
    login_url = reverse_lazy("account_login")
    permanent = False

    def get_redirect_url(self):
        if self.request.user.has_valid_password:
            return reverse("users:detail", kwargs={"pk": self.request.user.id})
        return reverse_lazy("users:set_password")


user_redirect_view = UserRedirectView.as_view()


class UserSetPasswordView(FormView, LoginRequiredMixin, SuccessMessageMixin):
    login_url = reverse_lazy("account_login")
    form_class = UserSetPasswordForm
    template_name = "users/user_set_password.html"
    success_message = "User successfully set password!"
    success_url = "/about"

    def form_valid(self, form):
        form.save(self.request.user)
        # See django docs:
        # https://docs.djangoproject.com/en/dev/topics/auth/default/#django.contrib.auth.update_session_auth_hash
        update_session_auth_hash(self.request, self.request.user)
        return super().form_valid(form)


user_set_password_view = UserSetPasswordView.as_view()
