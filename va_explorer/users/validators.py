import re

from django.contrib.auth.hashers import check_password
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from va_explorer.users.models import User, UserPasswordHistory


class PasswordComplexityValidator:
    def __init__(self):
        self.password_no_number = False
        self.password_no_uppercase = False
        self.password_no_lowercase = False
        self.password_no_special = False

    def validate(self, password, user=None):
        validation_errors = []
        if not re.findall(r"\d", password):
            self.password_no_number = True
            validation_errors.append(
                ValidationError(
                    _("Password requires at least one number"),
                    code="password_no_number",
                )
            )
        if not re.findall("[A-Z]", password):
            self.password_no_uppercase = True
            validation_errors.append(
                ValidationError(
                    _(
                        "Password requires at least one uppercase letter from \
                         the Latin alphabet (A-Z)"
                    ),
                    code="password_no_uppercase",
                )
            )
        if not re.findall("[a-z]", password):
            self.password_no_lowercase = True
            validation_errors.append(
                ValidationError(
                    _(
                        "Password requires at least one lowercase letter from \
                         the Latin alphabet (a-z)"
                    ),
                    code="password_no_lowercase",
                )
            )
        if not any(char in "!@#$%^&*()_+-=[]{}|'" for char in password):
            self.password_no_special = True
            validation_errors.append(
                ValidationError(
                    _(
                        "Password requires at least one nonalphanumeric \
                         character ! @ # $ % ^ & * ( ) _ + - = [ ] { } | '"
                    ),
                    code="password_no_special",
                )
            )
        if len(validation_errors) > 0:
            raise ValidationError(validation_errors)

    def get_help_text(self):
        return _(
            "Your password requires at least one number, one lowercase letter, \
             one uppercase letter, and one nonalphanumeric \
             character ! @ # $ % ^ & * ( ) _ + - = [ ] { } | '"
        )


class PasswordHistoryValidator:
    def __init__(self, history=12):
        self.history = history

    def validate(self, password, user=None):
        for last_password in self._get_last_passwords(user):
            if check_password(password=password, encoded=last_password):
                raise ValidationError(
                    _(
                        "Password must not be reused from the previous {} passwords."
                    ).format(self.history),
                    code="password_no_reuse",
                    params={"history": self.history},
                )

    def get_help_text(self):
        return _("Password must not be reused from the previous {} passwords.").format(
            self.history
        )

    def _get_last_passwords(self, user):
        user_password_history = UserPasswordHistory.objects.filter(
            user_id=user
        ).order_by("id")
        relevant = user_password_history.count() - self.history
        # Cleanup older history that we no longer care about if needed
        relevant = relevant if relevant > 0 else None  # prevents negative indexing
        if relevant:
            UserPasswordHistory.objects.filter(
                pk__in=user_password_history[0:relevant]
            ).delete()

        return [entry.old_password for entry in user_password_history[relevant:]]


# TODO: convert these to validator classes
# validate raw user data (from csv) against final user object
def validate_user_object(user_data, user_object=None):
    if not user_object:
        user_object = User.objects.filter(email=user_data["email"]).first()
        assert user_object

    # ensure credentials and group name check out
    assert re.sub("s$", "", user_object.groups.first().name.lower()) == re.sub(
        "s$", "", user_data["group"].lower()
    )
    assert user_object.name == user_data["name"]
    assert user_object.email == user_data["email"]

    # Only validate permissions that aren't set by group. If you create new
    # permissions types, need to add them below.
    # Assumes each permission X maps to a user getter starting with
    # 'can' (e.g. view_pii -> user.can_view_pii)
    for permission in ["view_pii", "download_data"]:
        is_group_permission = (
            user_object.groups.first().permissions.filter(codename=permission).first()
        )
        if not is_group_permission:
            assert getattr(user_object, f"can_{permission}") == user_data[permission]

    # if location restrictions for user, ensure all verbal autopsies fall
    # within their jurisdiction
    if (
        "location_restrictions" in user_data
        and len(user_data["location_restrictions"]) > 0
    ):
        jurisdiction = set(
            user_object.location_restrictions.first().get_descendant_ids()
        )
        va_locations = set(
            user_object.verbal_autopsies().values_list("location", flat=True)
        )
        assert va_locations.issubset(jurisdiction)


# validate raw user data (from csv) against user form output (before creating user)
def validate_user_form(user_data, user_form):
    # first, check if form is valid
    assert user_form.is_valid()
    form_data = user_form.cleaned_data
    assert re.sub("s$", "", form_data["group"].name.lower()) == re.sub(
        "s$", "", user_data["group"].lower()
    )
    assert form_data["download_data"] == user_data["download_data"]
    assert form_data["view_pii"] == user_data["view_pii"]
    assert form_data["email"] == user_data["email"]
    assert form_data["name"] == user_data["name"]

    if len(user_data.get("location_restrictions", [])) > 0:
        assert (
            form_data["location_restrictions"].first().name
            == user_data["location_restrictions"]
        )
