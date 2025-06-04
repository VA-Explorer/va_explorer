from django.contrib import messages
from django.contrib.auth import get_user_model, update_session_auth_hash
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import (
    CreateView,
    DetailView,
    FormView,
    ListView,
    RedirectView,
    UpdateView,
)

from ..utils.mixins import CustomAuthMixin, UserDetailViewMixin
from .forms import (
    ExtendedUserCreationForm,
    UserChangePasswordForm,
    UserSetPasswordForm,
    UserUpdateForm,
)

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
        kw = super().get_form_kwargs()
        kw["request"] = self.request  # the trick!
        return kw

    def form_valid(self, form):
        return super().form_valid(form)


user_create_view = UserCreateView.as_view()


class UserDetailView(CustomAuthMixin, UserDetailViewMixin, DetailView):
    login_url = reverse_lazy("account_login")
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
        # refresh the updated users session to apply their new role permissions
        user = User.objects.get(pk=self.kwargs["pk"])
        update_session_auth_hash(self.request, user)
        return super().form_valid(form)

    def get_initial(self):
        """
        Initializes the user's group on the form, which in our case is not done
        by default even though we are using a model-bound form. (Note that Group
        is a model from django.contrib.auth that is m2m with User.) We want to
        permit a user to be assigned to one Group only and thus must manually
        initialize the UpdateForm since we are imposing a change on the relation
        through how we allow the user to be assigned to groups.

        Initializes the user's geographic access on the form:
            (1) Set the national or location-specific geographic access. If
            there are any locations restrictions associated with the user in the
            database, they have location-specific access; else national access.
            (2) Set the facilities restrictions associated with the user, if any
        """
        initial = super().get_initial()

        initial["group"] = self.get_object().groups.first()
        initial["geographic_access"] = (
            "location-specific"
            if self.get_object().location_restrictions.exists()
            else "national"
        )
        initial["facility_restrictions"] = (
            self.get_object().location_restrictions.filter(location_type="facility")
        )

        initial["view_pii"] = self.get_object().can_view_pii
        initial["download_data"] = self.get_object().can_download_data

        return initial

    # TODO: Remove if we do not require email confirmation; we will no longer
    # need the lines below
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
            return reverse("home:index")
        return reverse_lazy("users:set_password")


user_redirect_view = UserRedirectView.as_view()


class UserSetPasswordView(FormView, LoginRequiredMixin, SuccessMessageMixin):
    """
    Allows the user to set a password of their choosing after logging in with a
    system-defined random password.

    If the user already has valid password, the system will redirect from this view

    Note: This URL is not linked anywhere in the application. Rather, a user is
    redirected to it if they do not have a valid password via the CustomAuthMixin.
    The redirect in the dispatch is set up in case the user types the URL in manually
    """

    login_url = reverse_lazy("account_login")
    form_class = UserSetPasswordForm
    template_name = "users/user_set_password.html"
    success_url = "/about"

    def dispatch(self, request, *args, **kwargs):
        if request.user.has_valid_password:
            messages.add_message(
                request, messages.INFO, "User has already set password."
            )
            # TODO: change redirect to something like a "home" page
            return redirect("/about")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.save(self.request.user)
        # See django docs:
        # https://docs.djangoproject.com/en/dev/topics/auth/default/#django.contrib.auth.update_session_auth_hash
        update_session_auth_hash(self.request, self.request.user)
        messages.success(self.request, "Password successfully set!")
        return super().form_valid(form)


user_set_password_view = UserSetPasswordView.as_view()


class UserChangePasswordView(FormView, LoginRequiredMixin, SuccessMessageMixin):
    """
    Allows the user to change their password if they already have a valid
    (i.e., non-temporary) password.
    """

    login_url = reverse_lazy("account_login")
    form_class = UserChangePasswordForm
    template_name = "users/user_change_password.html"
    success_message = "Password successfully changed!"
    # TODO: change success_url to something like a "home" page
    success_url = "/about"
    model = User

    # Sending user object to the form
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update({"user": self.request.user})
        return kwargs

    def form_valid(self, form):
        form.save(self.request.user)
        # See django docs:
        # https://docs.djangoproject.com/en/dev/topics/auth/default/#django.contrib.auth.update_session_auth_hash
        update_session_auth_hash(self.request, self.request.user)
        messages.success(self.request, "Password successfully changed!")
        return super().form_valid(form)


user_change_password_view = UserChangePasswordView.as_view()
