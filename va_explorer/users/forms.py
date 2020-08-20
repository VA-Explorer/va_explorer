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
from django.forms import ModelMultipleChoiceField
from django.utils.crypto import get_random_string

# from allauth.account.utils import send_email_confirmation, setup_user_email
# from django.forms import ModelChoiceField
from verbal_autopsy.models import Location

User = get_user_model()


# TODO: Allow for selection of only one group
# class ModelChoiceField(forms.ModelChoiceField):
#     def label_from_instance(self, obj):
#         return "%s" % (obj.name)


# TODO: Update to Django 3.1 to get access to the instance via value without making another query
class LocationSelectMultiple(forms.SelectMultiple):
    def create_option(self, name, value, *args, **kwargs):
        option = super().create_option(name, value, *args, **kwargs)
        if value:
            instance = self.choices.queryset.get(pk=value)  # get instance
            option["attrs"]["data-depth"] = instance.depth  # set option attribute
            option["attrs"]["data-descendants"] = instance.descendant_ids
        return option


class ExtendedUserCreationForm(UserCreationForm):
    """
    Extends the built in UserCreationForm in several ways:

    * The username is not visible.
    * name field is added.
    * Data not saved by the default behavior of UserCreationForm is saved.
    """

    name = forms.CharField(required=True)
    password1 = None
    password2 = None
    groups = ModelMultipleChoiceField(queryset=Group.objects.all(), required=True)
    locations = ModelMultipleChoiceField(
        queryset=Location.objects.all().order_by("path"),
        required=True,
        widget=LocationSelectMultiple(attrs={"class": "location-select"}),
    )

    # TODO: Allow for selection of only one group
    # group = ModelChoiceField(queryset=Group.objects.all())

    class Meta:
        model = User
        fields = ["name", "email", "groups", "locations"]

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request", None)

        super(UserCreationForm, self).__init__(*args, **kwargs)

    def clean(self, *args, **kwargs):
        """
        Normal cleanup
        """
        cleaned_data = super(UserCreationForm, self).clean(*args, **kwargs)
        return cleaned_data

    def save(self, commit=True):
        """
        Saves the email and name properties after the normal
        save behavior is complete. Sets a random password, which the user must
        change upon initial login.
        """
        user = super(UserCreationForm, self).save(commit)

        if user:
            user.email = self.cleaned_data["email"]
            user.name = self.cleaned_data["name"]

            password = get_random_string(length=32)
            user.set_password(password)

            locations = self.cleaned_data["locations"]

            if commit:
                user.save()

                # You cannot associate the user with a location(s) until it’s been saved
                # https://docs.djangoproject.com/en/3.1/topics/db/examples/many_to_many/
                user.locations.add(*locations)

            # TODO: Allow for selection of only one group
            # Set the group chosen from the POST request
            # user.groups.set(self.request.POST.get("group"))

            # TODO: Remove if we do not require email confirmation; we will no longer need the lines below
            # See allauth:
            # https://github.com/pennersr/django-allauth/blob/c19a212c6ee786af1bb8bc1b07eb2aa8e2bf531b/allauth/account/utils.py
            # setup_user_email(self.request, user, [])

            get_adapter().send_new_user_mail(self.request, user, password)

        return user


class UserUpdateForm(forms.ModelForm):
    name = forms.CharField(required=True, max_length=100)
    groups = ModelMultipleChoiceField(queryset=Group.objects.all(), required=True)
    locations = ModelMultipleChoiceField(
        queryset=Location.objects.all().order_by("path"),
        required=True,
        widget=LocationSelectMultiple(attrs={"class": "location-select"}),
    )

    # TODO: Allow for selection of only one group
    # group = GroupModelChoiceField(queryset=Group.objects.all())

    class Meta:
        model = User
        fields = ["name", "email", "is_active", "groups", "locations"]

    def __init__(self, *args, **kwargs):
        # TODO: Remove if we do not require email confirmation; we will no longer need the lines below
        # self.request = kwargs.pop("request", None)

        # TODO: Allow for selection of only one group
        # current_group = current_user.groups.first()

        super(UserUpdateForm, self).__init__(*args, **kwargs)

    def clean(self, *args, **kwargs):
        """
        Normal cleanup
        """
        cleaned_data = super(forms.ModelForm, self).clean()
        return cleaned_data

    def save(self, commit=True):
        user = super(UserUpdateForm, self).save(commit)
        locations = self.cleaned_data["locations"]

        if commit:
            # You cannot associate the user with a location(s) until it’s been saved
            # https://docs.djangoproject.com/en/3.1/topics/db/examples/many_to_many/
            user.locations.clear()
            user.locations.add(*locations)

        # TODO: Remove if we do not require email confirmation; we will no longer need the lines below
        # If the email address was changed, we add the new email address
        # if user.email != self.cleaned_data["email"]:
        #     user.add_email_address(self.request, self.cleaned_data["email"])

        # See allauth:
        # https://github.com/pennersr/django-allauth/blob/c19a212c6ee786af1bb8bc1b07eb2aa8e2bf531b/allauth/account/utils.py
        # send_email_confirmation(self.request, user, signup=False)

        return user


class UserSetPasswordForm(PasswordVerificationMixin, forms.Form):
    # See allauth:
    # https://github.com/pennersr/django-allauth/blob/master/allauth/account/forms.py#L54
    # If we do not want this dependency, we can write our own clean method to ensure the
    # 2 typed-in passwords match.
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
