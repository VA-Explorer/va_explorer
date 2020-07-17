from allauth.account.adapter import get_adapter
from allauth.account.utils import send_email_confirmation, setup_user_email
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Fieldset, Layout
from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import Group

User = get_user_model()


class UniqueUserEmailField(forms.EmailField):
    """
    An EmailField which only is valid if no User has that email.
    """

    def validate(self, value):
        super(forms.EmailField, self).validate(value)
        try:
            User.objects.get(email=value)
            raise forms.ValidationError("Email already exists")
        except User.MultipleObjectsReturned:
            raise forms.ValidationError("Email already exists")
        except User.DoesNotExist:
            pass


class GroupModelChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return "%s %s" % (obj.id, obj.name)


class ExtendedUserCreationForm(UserCreationForm):
    """
    Extends the built in UserCreationForm in several ways:

    * Adds an email field, which uses the custom UniqueUserEmailField,
      that is, the form does not validate if the email address already exists
      in the User table.
    * The username is not visible.
    * first_name and last_name fields are added.
    * Data not saved by the default behavior of UserCreationForm is saved.
    """

    email = UniqueUserEmailField(required=True, label="Email address")
    first_name = forms.CharField(required=True, max_length=30)
    last_name = forms.CharField(required=True, max_length=30)
    password1 = None
    password2 = None
    group = GroupModelChoiceField(queryset=Group.objects.all())

    class Meta:
        model = User
        fields = ["first_name", "last_name", "email", "is_superuser", "group"]

    def __init__(self, *args, **kwargs):
        """
        Changes the order of fields, and removes the username field.
        """
        self.request = kwargs.pop("request", None)

        super(UserCreationForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()

        self.helper.layout = Layout(
            Fieldset(
                "first arg is the legend of the fieldset",
                "first_name",
                "last_name",
                "email",
                "is_superuser",
                "group",
            )
        )

    def clean(self, *args, **kwargs):
        """
        Normal cleanup
        """
        cleaned_data = super(UserCreationForm, self).clean(*args, **kwargs)
        return cleaned_data

    def save(self, commit=True):
        """
        Saves the email, first_name and last_name properties, after the normal
        save behavior is complete. Sets a random password, which the user can change
        when they confirm their email address.
        """

        # See allauth:
        # https://django-allauth.readthedocs.io/en/latest/advanced.html
        # As per docs: "The following adapter methods can be used to intervene in how User
        # instances are created and populated with data."
        adapter = get_adapter(self.request)
        user = adapter.new_user(self.request)
        adapter.save_user(self.request, user, self)

        # Set the group chosen from the POST request
        user.groups.set(self.request.POST.get("group"))

        # See allauth:
        # https://github.com/pennersr/django-allauth/blob/c19a212c6ee786af1bb8bc1b07eb2aa8e2bf531b/allauth/account/utils.py
        setup_user_email(self.request, user, [])

        # See allauth:
        # https://github.com/pennersr/django-allauth/blob/c19a212c6ee786af1bb8bc1b07eb2aa8e2bf531b/allauth/account/utils.py
        send_email_confirmation(self.request, user, signup=False)

        return user
