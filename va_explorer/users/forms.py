from allauth.account.adapter import get_adapter
from allauth.account.forms import (
    PasswordField,
    PasswordVerificationMixin,
    SetPasswordField,
)
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Field
from django import forms
from django.contrib.auth import get_user_model, password_validation
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import Group
from django.forms import ModelMultipleChoiceField
from django.forms.fields import ChoiceField
from django.forms.models import ModelChoiceField
from django.utils.crypto import get_random_string
from django_select2 import forms as s2forms

# from allauth.account.utils import send_email_confirmation, setup_user_email
# from django.forms import ModelChoiceField
from verbal_autopsy.models import Location

User = get_user_model()


# TODO: Allow for selection of only one group
# class ModelChoiceField(forms.ModelChoiceField):
#     def label_from_instance(self, obj):
#         return "%s" % (obj.name)

class CustomSelect(forms.Select):
    def __init__(self, attrs=None, choices=()):
        self.custom_attrs = {}
        super().__init__(attrs, choices)

    def create_option(self, name, value, label, selected, index, subindex=None, attrs=None):
        index = str(index) if subindex is None else "%s_%s" % (index, subindex)
        if attrs is None:
            attrs = {}
        option_attrs = self.build_attrs(self.attrs, attrs) if self.option_inherits_attrs else {}
        if selected:
            option_attrs.update(self.checked_attribute)
        if 'id' in option_attrs:
            option_attrs['id'] = self.id_for_label(option_attrs['id'], index)

        # setting the attributes here for the option
        if len(self.custom_attrs) > 0:
            if value in self.custom_attrs:
                custom_attr = self.custom_attrs[value]
                for k, v in custom_attr.items():
                    option_attrs.update({k: v})

        return {
            'name': name,
            'value': value,
            'label': label,
            'selected': selected,
            'index': index,
            'attrs': option_attrs,
            'type': self.input_type,
            'template_name': self.option_template_name,
        }


class LocationChoiceField(forms.ModelMultipleChoiceField):
    def label_from_instance(self, obj):
        self.widget.custom_attrs.update({obj.pk: {'class': obj.depth}})
        return obj.name


class ExtendedUserCreationForm(UserCreationForm):
    """
    Extends the built in UserCreationForm in several ways:

    * Adds an email field, which uses the custom UniqueUserEmailField,
      that is, the form does not validate if the email address already exists
      in the User table.
    * The username is not visible.
    * name field is added.
    * Data not saved by the default behavior of UserCreationForm is saved.
    """

    name = forms.CharField(required=True)
    password1 = None
    password2 = None
    groups = ModelMultipleChoiceField(queryset=Group.objects.all(), required=True)
    locations = LocationChoiceField(queryset=Location.objects.all().order_by('path'), widget=CustomSelect(attrs={'class': "js-example-basic-single", 'multiple': "multiple", "name": 'locations[]' }))
    # TODO: Allow for selection of only one group
    # group = ModelChoiceField(queryset=Group.objects.all())

    class Meta:
        model = User
        fields = ["name", "email", "groups"]

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request", None)

        super(UserCreationForm, self).__init__(*args, **kwargs)

        #self.fields['locations'].widget.queryset = Location.objects.all()

        # location_types = [elem['location_type'] for elem in
        #                   Location.objects.order_by('depth').values('location_type').distinct()]

        # for depth, location in enumerate(location_types):
        #     depth += 1
        #     klass = "hidden" if depth > 1 else None
        #
        #     self.fields['location_%s' % depth] = forms.ModelMultipleChoiceField(
        #         label=location.capitalize(),
        #         queryset=Location.objects.filter(location_type=location),
        #         widget=forms.SelectMultiple(attrs={'class': klass}))

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

            if commit:
                user.save()

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
    provinces = ModelMultipleChoiceField(queryset=Location.objects.filter(location_type='province'), required=True)
    districts = ModelMultipleChoiceField(queryset=Location.objects.filter(location_type='district'), required=True)
    facilities = ModelMultipleChoiceField(queryset=Location.objects.filter(location_type='facility'), required=True)

    # TODO: Allow for selection of only one group
    # group = GroupModelChoiceField(queryset=Group.objects.all())

    class Meta:
        model = User
        fields = ["name", "email", "is_active", "groups", "provinces", "districts", "facilities"]

    def __init__(self, *args, **kwargs):
        # TODO: Remove if we do not require email confirmation; we will no longer need the lines below
        # self.request = kwargs.pop("request", None)

        # TODO: Allow for selection of only one group
        # current_user = kwargs.pop("instance")
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
