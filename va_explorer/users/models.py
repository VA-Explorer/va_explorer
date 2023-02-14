import uuid
from datetime import datetime
from functools import reduce

from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser, Permission
from django.db import models
from django.db.models import ManyToManyField
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

# from allauth.account.models import EmailAddress
# from allauth.account.signals import email_confirmed
# from django.dispatch import receiver
from va_explorer.va_data_management.models import Location, VerbalAutopsy


class CustomUserManager(BaseUserManager):
    """
    Custom user model manager where email is the unique identifiers
    for authentication instead of username.
    """

    def create_user(self, email, password, **extra_fields):
        """
        Create and save a User with the given email and password.
        """
        if not email:
            raise ValueError(_("Email is required"))
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, email, password, **extra_fields):
        """
        Create and save a SuperUser with the given email and password.
        """
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError(_("Superuser must have is_staff=True."))
        if extra_fields.get("is_superuser") is not True:
            raise ValueError(_("Superuser must have is_superuser=True."))
        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.original_password = self.password

    email = models.EmailField(_("email address"), unique=True)
    name = models.CharField(_("Name of User"), blank=True, max_length=255)
    has_valid_password = models.BooleanField(
        _("The user has a user-defined password"), default=False
    )
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    location_restrictions = ManyToManyField(
        Location, related_name="users", db_table="users_user_location_restrictions"
    )

    # The query set of verbal autopsies that this user has access to, based on
    # location restrictions
    # Note: locations are organized in a tree structure, and users have access
    # to all children of any parent location nodes they have access to
    def verbal_autopsies(self, date_cutoff=None, end_date=None):
        # only pull in VAs after certain time period. By default, everything after
        # 1901 (should be everything)
        date_cutoff = date_cutoff if date_cutoff else "1901-01-01"
        end_date = end_date if end_date else datetime.today().strftime("%Y-%m-%d")
        va_objects = VerbalAutopsy.objects.filter(
            Id10023__gte=date_cutoff, Id10023__lte=end_date
        )

        if self.location_restrictions.count() > 0:
            # Get the query set of all locations at or below the parent nodes
            # the user can access by joining the query sets of all the location
            # trees; using the | operator leads to an efficient query
            location_sets = [
                Location.get_tree(location)
                for location in self.location_restrictions.all()
            ]
            locations = reduce((lambda set1, set2: set1 | set2), location_sets)
            # Return the list of all verbal autopsies associated with that
            # query set of locations
            return va_objects.filter(location__in=locations)
        else:
            # No location restrictions, which implies access to all data
            return va_objects

    def is_fieldworker(self):
        return self.groups.filter(name="Field Workers").exists()

    @property
    def can_view_pii(self):
        return self.has_perm("va_analytics.view_pii")

    @can_view_pii.setter
    def can_view_pii(self, value):
        permission = Permission.objects.get(
            content_type__app_label="va_analytics", codename="view_pii"
        )
        if value:
            self.user_permissions.add(permission)
        else:
            self.user_permissions.remove(permission)

    @property
    def can_download_data(self):
        return self.has_perm("va_analytics.download_data")

    @can_download_data.setter
    def can_download_data(self, value):
        permission = Permission.objects.get(
            content_type__app_label="va_analytics", codename="download_data"
        )
        if value:
            self.user_permissions.add(permission)
        else:
            self.user_permissions.remove(permission)

    @property
    def can_supervise_users(self):
        return self.has_perm("va_analytics.supervise_users")

    @can_supervise_users.setter
    def can_supervise_users(self, value):
        permission = Permission.objects.get(
            content_type__app_label="va_analytics", codename="supervise_users"
        )
        if value:
            self.user_permissions.add(permission)
        else:
            self.user_permissions.remove(permission)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    def __str__(self):
        return self.email

    def get_absolute_url(self):
        """Get url for user's detail view.

        Returns:
            str: URL for user detail.

        """
        return reverse("users:detail", kwargs={"pk": self.pk})

    # TODO: Remove if we do not require email confirmation; we will no longer
    # need the lines below
    # def add_email_address(self, request, new_email):
    #     return EmailAddress.objects.add_email(
    #         request, self.user, new_email, confirm=True
    #     )
    #
    # @receiver(email_confirmed)
    # def update_user_email(sender, email_address, **kwargs):
    #     email_address.set_as_primary()
    #
    #     EmailAddress.objects.filter(
    #         user=email_address.user).exclude(primary=True).delete()

    def save(self, *args, **kwargs):
        # TODO: May need to be changed depending on how username comes in from ODK?
        if not self.username:
            self.username = self.email
        super().save(*args, **kwargs)
        if self.original_password != self.password:
            UserPasswordHistory.remember_password(self)


class UserPasswordHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    old_password = models.CharField(max_length=128)
    auto_now_add = True

    @classmethod
    def remember_password(cls, user):
        cls(user=user, old_password=user.password).save()
