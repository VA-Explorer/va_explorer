from unittest import TestCase

import pytest
from django.core.exceptions import ValidationError

from va_explorer.tests.factories import UserFactory
from va_explorer.users.models import UserPasswordHistory
from va_explorer.users.validators import (
    PasswordComplexityValidator,
    PasswordHistoryValidator,
)

pytestmark = pytest.mark.django_db


class TestPasswordComplexityValidator(TestCase):
    def setUp(self):
        self.user = UserFactory.create()
        self.validator = PasswordComplexityValidator()

    def test_rejects_no_number(self):
        with pytest.raises(ValidationError, match="number"):
            self.validator.validate("Password!", self.user)

    def test_rejects_no_lower(self):
        with pytest.raises(ValidationError, match="lowercase"):
            self.validator.validate("PASSWORD!", self.user)

    def test_rejects_no_upper(self):
        with pytest.raises(ValidationError, match="uppercase"):
            self.validator.validate("password!", self.user)

    def test_rejects_no_special(self):
        with pytest.raises(ValidationError, match="nonalphanumeric"):
            self.validator.validate("Password", self.user)

    def test_rejects_multiple(self):
        # Expect no_number, no_upper, and no_special in that order
        with pytest.raises(
            ValidationError, match="(number).*(uppercase).*(nonalphanumeric)"
        ):
            self.validator.validate("pass", self.user)

    def test_accepts_complex_password(self):
        try:
            self.validator.validate("Password1!", self.user)
        except ValidationError:
            self.fail("PasswordComplexityValidator raised ValidationError unexpectedly")


class TestPasswordHistoryValidator(TestCase):
    def setUp(self):
        self.user = UserFactory.create()
        self.validator = PasswordHistoryValidator()

    def test_accepts_new_password(self):
        try:
            self.validator.validate("test1", self.user)
        except ValidationError:
            self.fail("PasswordHistoryValidator raised ValidationError unexpectedly")

    def test_rejects_repeated_password(self):
        for i in range(0, 13):
            self.user.set_password(f"test{i}")
            self.user.save()

        with pytest.raises(ValidationError):
            self.validator.validate("test7", self.user)

    def test_keeps_limited_history(self):
        for i in range(0, 13):
            self.user.set_password(f"test{i}")
            self.user.save()

        self.validator.validate("new_password", self.user)
        password_history = UserPasswordHistory.objects.filter(user_id=self.user)
        assert password_history.count() == 12
