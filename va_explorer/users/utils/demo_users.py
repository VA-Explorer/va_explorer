from django.contrib.auth.models import Group

from va_explorer.users.models import User
from va_explorer.va_data_management.models import Location


def make_field_workers_for_facilities(facilities=None, num_per_facility=2):
    if not facilities:
        facilities = Location.objects.filter(location_type="facility").exclude(
            name="Unknown"
        )

    for i, facility in enumerate(facilities):
        for j in range(num_per_facility):
            worker_id = (i * num_per_facility) + j + 1
            create_demo_field_worker(worker_id, facility)


def create_demo_field_worker(worker_id, facility=None):
    username = f"field_worker_{worker_id}"

    user, created = User.objects.get_or_create(
        email=f"{username}@example.com",
        defaults={
            "name": f"Demo Field Worker {worker_id}",
            "is_active": True,
            "has_valid_password": True,
        },
    )

    if created:
        # assign password and save user
        user.set_password("Password1")
        user.save()

        # assign new user to field worker group
        user_group = Group.objects.get(name="Field Workers")
        user_group.user_set.add(user)
        # save user group changes
        user_group.save()

        # if facility name provided, assign field worker. Otherwise, randomly assign one
        if not facility:
            facility = (
                Location.objects.filter(location_type="facility").order_by("?").first()
            )

        user.location_restrictions.add(*[facility])

        # save/export final user
        user.save()

        print(
            f"Successfully created field worker with username {username} for \
            facility {facility.name}"
        )
