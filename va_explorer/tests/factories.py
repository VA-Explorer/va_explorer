import factory
from django.contrib.auth import get_user_model, models
from factory import DjangoModelFactory, Faker, Sequence
from factory.fuzzy import FuzzyInteger
from va_explorer.va_data_management.models import Location, VerbalAutopsy

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

    # Create a root node by default
    name = Faker("city")
    depth = 1
    numchild = 0
    location_type = "province"
    path = "0001"

class VerbalAutopsyFactory(DjangoModelFactory):
    class Meta:
        model = VerbalAutopsy
    Id10007 = "Example Name"
    location = factory.SubFactory(LocationFactory)

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


class FacilityFactory(LocationFactory):
    location_type = "facility"
