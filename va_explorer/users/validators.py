import re
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.hashers import check_password
from va_explorer.users.models import UserPasswordHistory


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
                        "Password requires at least one uppercase letter from Latin alphabet (A–Z)"
                    ),
                    code="password_no_uppercase",
                )
            )
        if not re.findall("[a-z]", password):
            self.password_no_lowercase = True
            validation_errors.append(
                ValidationError(
                    _(
                        "Password requires at least one lowercase letter from Latin alphabet (a-z)"
                    ),
                    code="password_no_lowercase",
                )
            )
        if not any(char in "!@#$%^&*()_+-=[]{}|'" for char in password):
            self.password_no_special = True
            validation_errors.append(
                ValidationError(
                    _(
                        "Password requires at least one nonalphanumeric character ! @ # $ % ^ & * ( ) _ + - = [ ] { } | '"
                    ),
                    code="password_no_special",
                )
            )
        if len(validation_errors) > 0:
            raise ValidationError(validation_errors)

    def get_help_text(self):
        validation_reqs = []
        if self.password_no_number:
            validation_reqs.append(_("Password requires at least one number"))
        if self.password_no_uppercase:
            validation_reqs.append(
                _(
                    "Password requires at least one uppercase letter from Latin alphabet (A–Z)"
                )
            )
        if self.password_no_lowercase:
            validation_reqs.append(
                _(
                    "Password requires at least one lowercase letter from Latin alphabet (a-z)"
                )
            )
        if self.password_no_special:
            validation_reqs.append(
                _(
                    "Password requires at least one nonalphanumeric character ! @ # $ % ^ & * ( ) _ + - = [ ] { } | '"
                )
            )
        return _("Password does not meet complexity requirements:\n").join(
            validation_reqs
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
        return _("Password must not be reused from the previous {} passwords.").format(self.history)

    def _get_last_passwords(self, user):
        user_password_history = UserPasswordHistory.objects.filter(user_id=user).order_by('id')
        relevant = user_password_history.count() - self.history
        # Cleanup older history that we no longer care about if needed
        relevant = relevant if relevant > 0 else None   # prevents negative indexing
        if relevant:
            UserPasswordHistory.objects.filter(pk__in=user_password_history[0:relevant]).delete()

        return [entry.old_password for entry in user_password_history[relevant:]]
