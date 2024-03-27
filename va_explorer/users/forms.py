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
from django.db.models import Q
from django.forms import (
    ModelChoiceField,
    ModelMultipleChoiceField,
    RadioSelect,
    SelectMultiple,
)
from django.utils.crypto import get_random_string

from va_explorer.va_data_management.models import Location

# from allauth.account.utils import send_email_confirmation, setup_user_email


User = get_user_model()


def get_location_restrictions(cleaned_data):
    """
    Utility method to determine if the user locations are from the location_restrictions
    dropdown or facility restrictions dropdown (Field Worker role only)
    """
    if (
        "location_restrictions" in cleaned_data
        and len(cleaned_data.get("facility_restrictions", [])) == 0
    ):
        return cleaned_data["location_restrictions"]
    elif (
        "facility_restrictions" in cleaned_data
        and len(cleaned_data.get("location_restrictions", [])) == 0
    ):
        return cleaned_data["facility_restrictions"]
    else:
        return []


def validate_location_access(form, geographic_access, location_restrictions, group):
    """
    Custom form validations related to geographic access and location restrictions
    """
    if group.name == "Field Workers":
        if len(location_restrictions) == 0 or geographic_access == "national":
            form._errors["facility_restrictions"] = form.error_class(
                ["You must add one or more facilities."]
            )
    else:
        if geographic_access == "location-specific" and len(location_restrictions) == 0:
            form._errors["location_restrictions"] = form.error_class(
                ["You must add one or more locations if access is location-specific."]
            )
        elif geographic_access == "national" and len(location_restrictions) > 0:
            form._errors["location_restrictions"] = form.error_class(
                ["You cannot add specific locations if access is national."]
            )


# core logic/steps to set user fields based on form data. Used in both UserCreation
# and ExtendedUserCreation forms
def process_user_data(user, cleaned_data):
    # set user location restrictions
    location_restrictions = get_location_restrictions(cleaned_data)
    user.location_restrictions.set(location_restrictions)

    # set user group
    group = cleaned_data["group"]
    user.groups.set([group])

    # if View PII permission specified in form, override user group's default permission
    if "view_pii" in cleaned_data:
        user.can_view_pii = cleaned_data["view_pii"]

    # if download data permission specified in form, override user group's
    # default permission
    if "download_data" in cleaned_data:
        user.can_download_data = cleaned_data["download_data"]

    user.save()
    return user


class LocationRestrictionsSelectMultiple(SelectMultiple):
    def create_option(
        self, name, value, label, selected, index, subindex=None, attrs=None
    ):
        option = super().create_option(
            name, value, label, selected, index, subindex, attrs
        )
        if value:
            # Use depth - 1 to account for root/country node
            option["attrs"]["data-depth"] = value.instance.depth - 1
            # Only query for descendants if there are any
            if value.instance.numchild > 0:
                option["attrs"][
                    "data-descendants"
                ] = value.instance.get_descendant_ids()
        return option


class GroupSelect(forms.Select):
    """
    Custom widget for group select that will have a 'data-view-pii' and
    'data-download-data' attributes.
    We can use this attribute in the HTML to determine whether or not to
    enable the 'Can View PII' checkbox.
    """

    def create_option(
        self, name, value, label, selected, index, subindex=None, attrs=None
    ):
        option = super().create_option(
            name, value, label, selected, index, subindex, attrs
        )
        if value:
            if value.instance.permissions.filter(codename="view_pii").first():
                option["attrs"]["data-view-pii"] = 1
            if value.instance.permissions.filter(codename="download_data").first():
                option["attrs"]["data-download-data"] = 1
        return option


class UserCommonFields(forms.ModelForm):
    name = forms.CharField(required=True, max_length=100)
    group = ModelChoiceField(
        queryset=Group.objects.all(), required=True, widget=GroupSelect
    )
    location_restrictions = ModelMultipleChoiceField(
        # Don't include 'Unknown' or Root/Country node in options
        queryset=Location.objects.all()
        .exclude(Q(location_type="country") | Q(name="Unknown"))
        .order_by("path"),
        widget=LocationRestrictionsSelectMultiple(
            attrs={"class": "location-restrictions-select"}
        ),
        required=False,
    )
    facility_restrictions = ModelMultipleChoiceField(
        queryset=Location.objects.filter(location_type="facility").order_by("name"),
        widget=forms.SelectMultiple(attrs={"class": "facility-restrictions-select"}),
        required=False,
        help_text="Field Workers must be assigned to at least one facility.",
    )
    geographic_access = forms.ChoiceField(
        choices=(("national", "National"), ("location-specific", "Location-specific")),
        initial="location-specific",
        widget=RadioSelect(),
        required=True,
    )
    view_pii = forms.BooleanField(
        label="Can View PII",
        help_text="Determines whether user can view PII. Only applies if group \
                   does not already grant access to view PII.",
        required=False,
    )
    download_data = forms.BooleanField(
        label="Can Download Data",
        help_text="Determines whether user can download data. Only applies if \
                   group does not already grant access to download data.",
        required=False,
    )


class ExtendedUserCreationForm(UserCommonFields, UserCreationForm):
    """
    Extends the built in UserCreationForm in several ways:

    * Name field is added.
    * Group model from django.contrib.auth.models is represented as a ModelChoiceField
    * Non-model field geographic_access added to toggle between national and
      location-specific access
    * Data not saved by the default behavior of UserCreationForm is saved.
    """

    password1 = None
    password2 = None

    class Meta:
        model = User
        fields = [
            "name",
            "email",
            "group",
            "view_pii",
            "download_data",
            "geographic_access",
            "location_restrictions",
            "facility_restrictions",
        ]

    def __init__(self, *args, **kwargs):
        """
        Set the request on the form class so that we can access the request when
        calling send_new_user_mail() in the save method below
        """
        self.request = kwargs.pop("request", None)

        super(UserCreationForm, self).__init__(*args, **kwargs)

        self.fields["group"].label = "Role"

    def clean(self, *args, **kwargs):
        """
        Normal cleanup
        """
        cleaned_data = super(UserCreationForm, self).clean(*args, **kwargs)

        if "geographic_access" and "group" in cleaned_data:
            location_restrictions = get_location_restrictions(cleaned_data)

            validate_location_access(
                self,
                cleaned_data["geographic_access"],
                location_restrictions,
                cleaned_data["group"],
            )

        return cleaned_data

    def save(self, commit=True, email_confirmation=True):
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

            password = get_random_string(length=16)
            user.set_password(password)

            # location_restrictions = get_location_restrictions(self.cleaned_data)
            # group = self.cleaned_data["group"]

            if commit:
                # Need to save again after setting password.
                user.save()
                user = process_user_data(user, self.cleaned_data)

            # TODO: Remove if we do not require email confirmation; we will no
            # longer need the lines below. See allauth:
            # https://github.com/pennersr/django-allauth/blob/c19a212c6ee786af1bb8bc1b07eb2aa8e2bf531b/allauth/account/utils.py
            # setup_user_email(self.request, user, [])
            # A workaround to run this script without a mail server.
            # If True, it will send email like normal.
            # If False, user credentials will just be printed to console.
            console_msg = (
                "" * 20
                + f"Created user with email {user.email} and temp. password {password}"
            )
            if email_confirmation:
                try:
                    get_adapter().send_new_user_mail(self.request, user, password)
                except Exception as err:
                    print("WARNING: failed to send email. Printing credentials instead")
                    print(console_msg)
                    print(f"Failure source: {err}")

            else:
                print(console_msg)

        return user


class UserUpdateForm(UserCommonFields, forms.ModelForm):
    """
    Similar to UserCreationForm but adds is_active field to allow an administrator
    to mark a user account as inactive
    """

    class Meta:
        model = User
        fields = [
            "name",
            "email",
            "is_active",
            "group",
            "view_pii",
            "download_data",
            "geographic_access",
            "location_restrictions",
            "facility_restrictions",
        ]

    def __init__(self, *args, **kwargs):
        # TODO: Remove if we do not require email confirmation; we will no longer
        # need the lines below

        super().__init__(*args, **kwargs)
        self.fields["group"].label = "Role"

    def clean(self, *args, **kwargs):
        """
        Normal cleanup
        """
        cleaned_data = super(forms.ModelForm, self).clean()

        if "geographic_access" and "group" in cleaned_data:
            location_restrictions = get_location_restrictions(cleaned_data)

            validate_location_access(
                self,
                cleaned_data["geographic_access"],
                location_restrictions,
                cleaned_data["group"],
            )

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit)

        if commit:
            # only run va matching logic when user is first created
            user = process_user_data(user, self.cleaned_data)

        return user


class UserSetPasswordForm(PasswordVerificationMixin, forms.Form):
    """
    Allows the user to set a password of their choosing after logging in with a
    system-defined random password.

    See allauth:
        https://github.com/pennersr/django-allauth/blob/master/allauth/account/forms.py#L54
        If we do not want this dependency, we can write our own clean method to
        ensure the 2 typed-in passwords match.
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
    Allows the user to change their password if they already have a valid
    (i.e., non-temporary) password. Requires the user to re-type their old
    password and type in their new password twice.

    See allauth:
        https://github.com/pennersr/django-allauth/blob/master/allauth/account/forms.py#L54
        If we do not want this dependency, we can write our own clean method to
        ensure the 2 typed-in passwords match.
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
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

    def clean_current_password(self):
        if not self.user.check_password(self.cleaned_data.get("current_password")):
            raise forms.ValidationError("Please type your current password.")
        return self.cleaned_data["current_password"]

    def save(self, user):
        user.set_password(self.cleaned_data["password1"])
        user.save()

        return user
