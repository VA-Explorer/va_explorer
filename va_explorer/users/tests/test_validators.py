from unittest import TestCase
import pytest
from django.core.exceptions import ValidationError
from va_explorer.tests.factories import UserFactory
from va_explorer.users.models import UserPasswordHistory
from va_explorer.users.validators import PasswordHistoryValidator


pytestmark = pytest.mark.django_db


class TestPasswordHistoryValidator(TestCase):
    def setUp(self):
        self.user = UserFactory.create()
        self.validator = PasswordHistoryValidator()

    def test_accepts_new_password(self):
        try:
            self.validator.validate('test1', self.user)
        except ValidationError:
            self.fail("PasswordHistoryValidator raised ValidationError unexpectedly")

    def test_rejects_repeated_password(self):
        for i in range(0, 13):
            self.user.set_password(f"test{i}")
            self.user.save()

        with self.assertRaises(ValidationError):
            self.validator.validate("test7", self.user)

    def test_keeps_limited_history(self):
        for i in range(0, 13):
            self.user.set_password(f"test{i}")
            self.user.save()

        self.validator.validate("new_password", self.user)
        password_history = UserPasswordHistory.objects.filter(username_id=self.user)
        self.assertEqual(password_history.count(), 12)
