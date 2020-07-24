# from allauth.account.models import EmailAddress
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand

User = get_user_model()


class Command(BaseCommand):
    help = "Seeds data manager, data viewer, and field worker users"

    def handle(self, *args, **options):
        find_or_create_data_manager(self)
        find_or_create_data_viewer(self)
        find_or_create_field_worker(self)


def find_or_create_data_manager(self):
    self.stdout.write(self.style.SUCCESS("Creating a data manager..."))

    data_manager, created = User.objects.get_or_create(
        email="data_manager@example.com",
        defaults={
            "name": "Data Manager",
            "is_active": True,
            "has_valid_password": True,
        },
    )

    if created:
        data_manager.set_password("Password1")
        data_manager.save()

        data_manager_group = Group.objects.get(name="Data Managers")
        data_manager_group.user_set.add(data_manager)

        data_manager_group.save()

        # If we do not require email confirmation, we no longer need the lines below
        # EmailAddress.objects.create(
        #     user=data_manager, email=data_manager.email, verified=True, primary=True
        # )

        self.stdout.write(self.style.SUCCESS("Successfully created a data manager!"))


def find_or_create_data_viewer(self):
    self.stdout.write(self.style.SUCCESS("Creating a data viewer..."))

    data_viewer, created = User.objects.get_or_create(
        email="data_viewer@example.com",
        defaults={"name": "Data Viewer", "is_active": True, "has_valid_password": True},
    )

    if created:
        data_viewer.set_password("Password1")
        data_viewer.save()

        data_viewer_group = Group.objects.get(name="Data Viewers")
        data_viewer_group.user_set.add(data_viewer)

        data_viewer_group.save()

        # If we do not require email confirmation, we no longer need the lines below
        # EmailAddress.objects.create(
        #     user=data_viewer, email=data_viewer.email, verified=True, primary=True
        # )

        self.stdout.write(self.style.SUCCESS("Successfully created a data viewer!"))


def find_or_create_field_worker(self):
    self.stdout.write(self.style.SUCCESS("Creating a field worker..."))

    field_worker, created = User.objects.get_or_create(
        email="field_worker@example.com",
        defaults={
            "name": "Field Worker",
            "is_active": True,
            "has_valid_password": True,
        },
    )

    if created:
        field_worker.set_password("Password1")
        field_worker.save()

        field_worker_group = Group.objects.get(name="Field Workers")
        field_worker_group.user_set.add(field_worker)

        field_worker_group.save()

        # If we do not require email confirmation, we no longer need the lines below
        # EmailAddress.objects.create(
        #     user=field_worker, email=field_worker.email, verified=True, primary=True
        # )

        self.stdout.write(self.style.SUCCESS("Successfully created a field worker!"))
