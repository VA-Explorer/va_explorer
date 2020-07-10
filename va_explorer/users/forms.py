from crispy_forms.helper import FormHelper
from crispy_forms.layout import Fieldset, Layout
from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm

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


class ExtendedUserCreationForm(UserCreationForm):
    """
    Extends the built in UserCreationForm in several ways:

    * Adds an email field, which uses the custom UniqueUserEmailField,
      that is, the form does not validate if the email address already exists
      in the User table.
    * The username field is generated based on the email, and isn't visible.
    * first_name and last_name fields are added.
    * Data not saved by the default behavior of UserCreationForm is saved.
    """

    email = UniqueUserEmailField(required=True, label="Email address")
    first_name = forms.CharField(required=True, max_length=30)
    last_name = forms.CharField(required=True, max_length=30)
    password1 = None
    password2 = None

    class Meta:
        model = User
        fields = ["first_name", "last_name", "email", "is_superuser"]

    def __init__(self, *args, **kwargs):
        """
        Changes the order of fields, and removes the username field.
        """
        super(UserCreationForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Fieldset(
                "first arg is the legend of the fieldset",
                "first_name",
                "last_name",
                "email",
                "is_superuser",
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
        user = super(UserCreationForm, self).save(commit)
        if user:
            user.email = self.cleaned_data["email"]
            user.first_name = self.cleaned_data["first_name"]
            user.last_name = self.cleaned_data["last_name"]
            user.is_superuser = self.cleaned_data["is_superuser"]
            password = User.objects.make_random_password()
            user.set_password(password)
            user.username = user.email
            if commit:
                user.save()
        return user
