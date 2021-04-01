from django.contrib.auth import get_permission_codename
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.core.management import BaseCommand

from va_explorer.va_analytics.models import Dashboard
from va_explorer.va_data_management.models import VerbalAutopsy

User = get_user_model()

GROUPS_PERMISSIONS = {
    "Admins": {
        Dashboard: ["view"],
        User: ["add", "change", "delete", "view"],
        VerbalAutopsy: ["change", "view"],
    },
    "Data Managers": {
        Dashboard: ["view"],
        User: ["view"],
        VerbalAutopsy: ["change", "view"],
    },
    "Data Viewers": {
        Dashboard: ["view"],
        User: [],
        VerbalAutopsy: ["view"],
    },
    "Field Workers": {
        Dashboard: [],
        User: [],
        VerbalAutopsy: ["view"]
    },
}


class Command(BaseCommand):
    def __init__(self, *args, **kwargs):
        super(Command, self).__init__(*args, **kwargs)

    help = "Create default groups and permissions"

    def handle(self, *args, **options):
        # Loop through groups and permissions; add permissions, as applicable, to related group objects
        for group_name, group_permissions in GROUPS_PERMISSIONS.items():
            group, created = Group.objects.get_or_create(name=group_name)

            """
            Delete the permissions if they exist

            Assumption:
            If we are running this script, permissions have changed and we want to
            recreate them
            """
            if group.permissions.exists():
                group.permissions.clear()

            for model_class, model_permissions in group_permissions.items():
                for model_permission_name in model_permissions:
                    codename = get_permission_codename(model_permission_name, model_class._meta)

                    try:
                        permission = Permission.objects.get(codename=codename)
                        group.permissions.add(permission)
                        self.stdout.write(f"Adding {codename} to group {group}")
                    except Permission.DoesNotExist:
                        self.stdout.write(f"{codename} not found")
