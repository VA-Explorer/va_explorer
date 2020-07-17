from allauth.account.models import EmailAddress
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
            "username": "data_manager",
            "first_name": "data",
            "last_name": "manager",
            "is_active": True,
        },
    )

    if created:
        data_manager.set_password("Password1")
        data_manager.save()

        data_manager_group = Group.objects.get(name="Data Managers")
        data_manager_group.user_set.add(data_manager)

        data_manager_group.save()

        # To avoid email verification, we add the below line to each user
        EmailAddress.objects.create(
            user=data_manager, email=data_manager.email, verified=True, primary=True
        )

        self.stdout.write(self.style.SUCCESS("Successfully created a data manager!"))


def find_or_create_data_viewer(self):
    self.stdout.write(self.style.SUCCESS("Creating a data viewer..."))

    data_viewer, created = User.objects.get_or_create(
        email="data_viewer@example.com",
        defaults={
            "username": "data_viewer",
            "first_name": "data",
            "last_name": "viewer",
            "is_active": True,
        },
    )

    if created:
        data_viewer.set_password("Password1")
        data_viewer.save()

        data_viewer_group = Group.objects.get(name="Data Viewers")
        data_viewer_group.user_set.add(data_viewer)

        data_viewer_group.save()

        # To avoid email verification, we add the below line to each user
        EmailAddress.objects.create(
            user=data_viewer, email=data_viewer.email, verified=True, primary=True
        )

        self.stdout.write(self.style.SUCCESS("Successfully created a data viewer!"))


def find_or_create_field_worker(self):
    self.stdout.write(self.style.SUCCESS("Creating a field worker..."))

    field_worker, created = User.objects.get_or_create(
        email="field_worker@example.com",
        defaults={
            "username": "field_worker",
            "first_name": "field",
            "last_name": "worker",
            "is_active": True,
        },
    )

    if created:
        field_worker.set_password("Password1")
        field_worker.save()

        field_worker_group = Group.objects.get(name="Field Workers")
        field_worker_group.user_set.add(field_worker)

        field_worker_group.save()

        EmailAddress.objects.create(
            user=field_worker, email=field_worker.email, verified=True, primary=True
        )

        self.stdout.write(self.style.SUCCESS("Successfully created a field worker!"))
