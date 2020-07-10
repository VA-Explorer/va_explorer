from django.contrib.auth import get_user_model
from factory import DjangoModelFactory, Faker


class UserFactory(DjangoModelFactory):

    username = Faker("user_name")
    email = Faker("email")
    first_name = Faker("first_name")
    last_name = Faker("last_name")

    class Meta:
        model = get_user_model()
        django_get_or_create = ["email"]
