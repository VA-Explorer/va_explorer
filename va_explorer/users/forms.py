from allauth.account.adapter import get_adapter
from allauth.account.forms import (
    PasswordField,
    PasswordVerificationMixin,
    SetPasswordField,
)
from django import forms
from django.contrib.auth import get_user_model, password_validation
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import Group
from django.forms import ModelChoiceField, ModelMultipleChoiceField, RadioSelect, SelectMultiple
from django.utils.crypto import get_random_string
from va_explorer.va_data_management.models import Location

# from allauth.account.utils import send_email_confirmation, setup_user_email


User = get_user_model()


# Assigns user to national-level access implicitly if no location_restrictions are associated with the user.
def validate_location_access(form, geographic_access, location_restrictions):
    if geographic_access == "location-specific" and len(location_restrictions) == 0:
        form._errors["location_restrictions"] = form.error_class(
            ["You must add one or more location_restrictions if access is location-specific."]
        )
    elif geographic_access == "national" and len(location_restrictions) > 0:
        form._errors["location_restrictions"] = form.error_class(
            ["You cannot add specific location_restrictions if access is national."]
        )


class LocationRestrictionsSelectMultiple(SelectMultiple):
    def create_option(self, name, value, label, selected, index, subindex=None, attrs=None):
        option = super().create_option(name, value, label, selected, index, subindex, attrs)
        if value:
            option['attrs']['data-depth'] = value.instance.depth
            # Only query for descendants if there are any
            if value.instance.numchild > 0:
                option['attrs']['data-descendants'] = value.instance.get_descendant_ids()
        return option


class ExtendedUserCreationForm(UserCreationForm):
    """
    Extends the built in UserCreationForm in several ways:

    * The username is not visible.
    * Name field is added.
    * Group model from django.contrib.auth.models is represented as a ModelChoiceField
    * Non-model field geographic_access added to toggle between national and location-specific access
    * Data not saved by the default behavior of UserCreationForm is saved.
    """

    name = forms.CharField(required=True)
    password1 = None
    password2 = None
    # Allows us to save one group for the user, even though groups are m2m with user by default
    group = ModelChoiceField(queryset=Group.objects.all(), required=True)
    location_restrictions = ModelMultipleChoiceField(
        queryset=Location.objects.all().order_by("path"),
        widget=LocationRestrictionsSelectMultiple(attrs={"class": "location-restrictions-select"}),
        required=False,
    )
    geographic_access = forms.ChoiceField(
        choices=(("national", "National"), ("location-specific", "Location-specific")),
        initial="location-specific",
        widget=RadioSelect(),
        required=True,
    )

    class Meta:
        model = User
        fields = ["name", "email", "group", "geographic_access", "location_restrictions"]

    def __init__(self, *args, **kwargs):
        """
        Set the request on the form class so that we can access the request when calling
        send_new_user_mail() in the save method below
        """
        self.request = kwargs.pop("request", None)

        super(UserCreationForm, self).__init__(*args, **kwargs)
        self.fields["group"].label = "Role"

    def clean(self, *args, **kwargs):
        """
        Normal cleanup
        """
        cleaned_data = super(UserCreationForm, self).clean(*args, **kwargs)

        if "geographic_access" in cleaned_data and "location_restrictions" in cleaned_data:
            validate_location_access(
                self, cleaned_data["geographic_access"], cleaned_data["location_restrictions"]
            )

        return cleaned_data

    def save(self, commit=True):
        """
        Saves the email and name properties after the normal
        save behavior is complete. Sets a random password, which the user must
        change upon initial login.

        Saves the location and group after the user object is saved.
        """
        user = super(UserCreationForm, self).save(commit)

        if user:
            user.email = self.cleaned_data["email"]
            user.name = self.cleaned_data["name"]

            password = get_random_string(length=32)
            user.set_password(password)

            location_restrictions = self.cleaned_data["location_restrictions"]
            group = self.cleaned_data["group"]

            if commit:
                user.save()

                # You cannot associate the user with a m2m field until it’s been saved
                # https://docs.djangoproject.com/en/3.1/topics/db/examples/many_to_many/
                user.location_restrictions.add(*location_restrictions)
                user.groups.add(*[group])

            # TODO: Remove if we do not require email confirmation; we will no longer need the lines below
            # See allauth:
            # https://github.com/pennersr/django-allauth/blob/c19a212c6ee786af1bb8bc1b07eb2aa8e2bf531b/allauth/account/utils.py
            # setup_user_email(self.request, user, [])

            get_adapter().send_new_user_mail(self.request, user, password)

        return user


class UserUpdateForm(forms.ModelForm):
    """
    Similar to UserCreationForm but adds is_active field to allow an administrator
    to mark a user account as inactive
    """

    name = forms.CharField(required=True, max_length=100)
    group = ModelChoiceField(queryset=Group.objects.all(), required=True)
    location_restrictions = ModelMultipleChoiceField(
        queryset=Location.objects.all().order_by("path"),
        widget=LocationRestrictionsSelectMultiple(attrs={"class": "location-restrictions-select"}),
        required=False,
    )
    geographic_access = forms.ChoiceField(
        choices=(("national", "National"), ("location-specific", "Location-specific")),
        widget=RadioSelect(),
        required=True,
    )

    class Meta:
        model = User
        fields = [
            "name",
            "email",
            "is_active",
            "group",
            "geographic_access",
            "location_restrictions",
        ]

    def __init__(self, *args, **kwargs):
        # TODO: Remove if we do not require email confirmation; we will no longer need the lines below
        # self.request = kwargs.pop("request", None)

        super(UserUpdateForm, self).__init__(*args, **kwargs)
        self.fields["group"].label = "Role"

    def clean(self, *args, **kwargs):
        """
        Normal cleanup
        """
        cleaned_data = super(forms.ModelForm, self).clean()

        if "geographic_access" in cleaned_data and "location_restrictions" in cleaned_data:
            validate_location_access(
                self, cleaned_data["geographic_access"], cleaned_data["location_restrictions"]
            )
        return cleaned_data

    def save(self, commit=True):
        user = super(UserUpdateForm, self).save(commit)
        location_restrictions = self.cleaned_data["location_restrictions"]
        group = self.cleaned_data["group"]

        if commit:
            """
            You cannot associate the user with a m2m field until it’s been saved
            https://docs.djangoproject.com/en/3.1/topics/db/examples/many_to_many/
            Set combines clear() and add(*location_restrictions)
            """
            user.location_restrictions.set(location_restrictions)
            user.groups.set([group])

        # TODO: Remove if we do not require email confirmation; we will no longer need the lines below
        # If the email address was changed, we add the new email address
        # if user.email != self.cleaned_data["email"]:
        #     user.add_email_address(self.request, self.cleaned_data["email"])

        """
        See allauth:
        https://github.com/pennersr/django-allauth/blob/c19a212c6ee786af1bb8bc1b07eb2aa8e2bf531b/allauth/account/utils.py
        send_email_confirmation(self.request, user, signup=False)
        """

        return user


class UserSetPasswordForm(PasswordVerificationMixin, forms.Form):
    """
    Allows the user to set a password of their choosing after logging in with a system-defined
    random password.

    See allauth:
        https://github.com/pennersr/django-allauth/blob/master/allauth/account/forms.py#L54
        If we do not want this dependency, we can write our own clean method to ensure the
        2 typed-in passwords match.
    """

    password1 = SetPasswordField(
        label="New Password",
        help_text=password_validation.password_validators_help_text_html(),
    )
    password2 = PasswordField(label="New Password (again)")

    def save(self, user):
        user.set_password(self.cleaned_data["password1"])
        user.has_valid_password = True
        user.save()

        return user


class UserChangePasswordForm(PasswordVerificationMixin, forms.Form):
    """
    Allows the user to change their password if they already have a valid (i.e., non-temporary) password.
    Requires the user to re-type their old password and type in their new password twice.

    See allauth:
        https://github.com/pennersr/django-allauth/blob/master/allauth/account/forms.py#L54
        If we do not want this dependency, we can write our own clean method to ensure the
        2 typed-in passwords match.
    """
    current_password = PasswordField(label="Current Password")

    password1 = SetPasswordField(
        label="New Password",
        help_text=password_validation.password_validators_help_text_html(),
    )
    password2 = PasswordField(label="New Password (again)")

    def __init__(self, *args, **kwargs):
        """
        Set the current user on the form
        We need this to call user.check_password in clean_current_password
        """
        self.user = kwargs.pop('user', None)
        super(UserChangePasswordForm, self).__init__(*args, **kwargs)

    def clean_current_password(self):
        if not self.user.check_password(self.cleaned_data.get("current_password")):
            raise forms.ValidationError(("Please type your current password."))
        return self.cleaned_data["current_password"]

    def save(self, user):
        user.set_password(self.cleaned_data["password1"])
        user.save()

        return user
