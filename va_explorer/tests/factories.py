import json

import factory
from django.contrib.auth import get_user_model, models
from factory import Faker, Sequence
from factory.django import DjangoModelFactory

from va_explorer.va_data_management.models import (
    CauseCodingIssue,
    CauseOfDeath,
    DhisStatus,
    Location,
    VerbalAutopsy,
)

User = get_user_model()


class PermissionFactory(DjangoModelFactory):
    class Meta:
        model = models.Permission


class GroupFactory(DjangoModelFactory):
    class Meta:
        model = models.Group

    name = Sequence(lambda n: f"Group #{n}")

    @factory.post_generation
    def permissions(self, create, extracted, **kwargs):
        if not create:
            # Simple build, do nothing.
            return

        if extracted:
            # A list of groups were passed in, use them
            for permission in extracted:
                self.permissions.add(permission)


class LocationFactory(DjangoModelFactory):
    class Meta:
        model = Location

    # Create a root node by default
    name = Faker("city")
    depth = 1
    numchild = 0
    location_type = "province"
    path = "0001"


class LocationFacilityFactory(DjangoModelFactory):
    class Meta:
        model = Location
        django_get_or_create = ("path",)

    # Create a root node by default
    name = Faker("city")
    depth = 1
    numchild = 0
    location_type = "facility"
    path = "0001"


class VerbalAutopsyFactory(DjangoModelFactory):
    class Meta:
        model = VerbalAutopsy

    Id10007 = "Example Name"
    Id10023 = "1901-01-01"
    Id10058 = "hospital"
    location = factory.SubFactory(LocationFacilityFactory)


class CauseOfDeathFactory(DjangoModelFactory):
    class Meta:
        model = CauseOfDeath

    cause = "HIV/AIDS related death"
    algorithm = "InterVA5"
    settings = json.dumps({"HIV": "l", "Malaria": "l"})
    verbalautopsy = factory.SubFactory(VerbalAutopsyFactory)


class UserFactory(DjangoModelFactory):
    class Meta:
        model = User

    email = Faker("email")
    name = Faker("name")
    has_valid_password = True

    # See: https://factoryboy.readthedocs.io/en/latest/recipes.html
    @factory.post_generation
    def groups(self, create, extracted, **kwargs):
        if not create:
            # Simple build, do nothing.
            return

        if extracted:
            # A list of groups were passed in, use them
            for group in extracted:
                self.groups.add(group)

    @factory.post_generation
    def location_restrictions(self, create, extracted, *kwargs):
        if not create:
            # Simple build, do nothing.
            return

        if extracted:
            # A list of locations were passed in, use them
            for location in extracted:
                self.location_restrictions.add(location)


class NewUserFactory(UserFactory):
    has_valid_password = False


class AdminFactory(UserFactory):
    is_superuser = True


class DataManagerFactory(UserFactory):
    is_superuser = False


class DataViewerFactory(UserFactory):
    is_superuser = False


class FieldWorkerFactory(UserFactory):
    is_superuser = False


class FieldWorkerGroupFactory(GroupFactory):
    name = "Field Workers"


class AdminGroupFactory(GroupFactory):
    name = "Admins"


class FacilityFactory(LocationFactory):
    location_type = "facility"


class CauseCodingIssueFactory(DjangoModelFactory):
    class Meta:
        model = CauseCodingIssue

    text = "Warning: field username, the va record does not have an assigned username."
    severity = "warning"
    settings = json.dumps({"HIV": "l", "Malaria": "l"})


class DhisStatusFactory(DjangoModelFactory):
    class Meta:
        model = DhisStatus
