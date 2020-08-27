import factory
from django.contrib.auth import get_user_model, models
from factory import DjangoModelFactory, Faker, Sequence
from factory.fuzzy import FuzzyInteger
from verbal_autopsy.models import Location

User = get_user_model()


class PermissionFactory(DjangoModelFactory):
    class Meta:
        model = models.Permission


class GroupFactory(DjangoModelFactory):
    class Meta:
        model = models.Group

    name = Sequence(lambda n: "Group #%s" % n)

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

    name = Faker("city")
    depth = FuzzyInteger(0, 4, 1)
    location_type = "district"
    numchild = FuzzyInteger(0, 20)
    path = "001"


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
    def locations(self, create, extracted, *kwargs):
        if not create:
            # Simple build, do nothing.
            return

        if extracted:
            # A list of groups were passed in, use them
            for location in extracted:
                self.locations.add(location)


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
