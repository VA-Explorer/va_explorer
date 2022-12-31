from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType

from va_explorer.tests.factories import LocationFactory, VerbalAutopsyFactory
from va_explorer.users.management.commands.initialize_groups import GROUPS_PERMISSIONS


def setup_test_db(with_vas=True):
    province = LocationFactory.create(name="Province1")
    district_x = province.add_child(name="DistrictX", location_type="district")
    facility1 = district_x.add_child(name="Facility1", location_type="facility")
    district_y = province.add_child(name="DistrictY", location_type="district")
    facility2 = district_y.add_child(name="Facility2", location_type="facility")
    facility3 = district_y.add_child(name="Facility3", location_type="facility")

    if with_vas:
        # Each facility with one VA
        VerbalAutopsyFactory.create(location=facility1)
        VerbalAutopsyFactory.create(location=facility2)
        VerbalAutopsyFactory.create(location=facility3)

    # create user groups defined in initialize_groups.py
    for group_name, group_permissions in GROUPS_PERMISSIONS.items():
        group, _ = Group.objects.get_or_create(name=group_name)
        if group.permissions.exists():
            group.permissions.clear()
        for model_class, model_permissions in group_permissions.items():
            for codename in model_permissions:
                # Get the content type for the given model class.
                content_type = ContentType.objects.get_for_model(model_class)

                # Lookup permission based on content type and codename.
                try:
                    permission = Permission.objects.get(
                        content_type=content_type, codename=codename
                    )
                    group.permissions.add(permission)
                except Exception as err:
                    print(f"Error: {err}")


# create three dummy users for testing, each with different roles, location
# restrictions, and privacy privileges
def get_fake_user_data():
    return {
        # user 1: restricted to location X, data viewer, cant view PII but can
        # download data
        "u1": {
            "name": "user1",
            "email": "user1@example.com",
            "location_restrictions": "DistrictX",
            "group": "Data Viewer",
            "view_pii": False,
            "download_data": True,
        },
        # user 2: data manager restricted to districtY, can view PII and can
        # download data
        "u2": {
            "name": "user2",
            "email": "user2@example.com",
            "location_restrictions": "DistrictY",
            "group": "Data Manager",
            "view_pii": True,
            "download_data": True,
        },
        # user 3: data viewer - no location restrictions, can view PII but cannot
        # download data
        "u3": {
            "name": "user3",
            "email": "user3@example.com",
            "group": "Data Viewer",
            "view_pii": True,
            "download_data": False,
        },
    }
