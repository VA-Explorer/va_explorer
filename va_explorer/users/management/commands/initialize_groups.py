from django.contrib.contenttypes.models import ContentType
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.contrib.auth.models import Permission
from django.core.management import BaseCommand

from va_explorer.va_analytics.models import Dashboard
from va_explorer.va_data_management.models import VerbalAutopsy

User = get_user_model()

GROUPS_PERMISSIONS = {
    "Admins": {
        Dashboard: ["view_dashboard", "download_data", "view_pii"],
        User: ["add_user", "change_user", "delete_user", "view_user"],
        VerbalAutopsy: ["change_verbalautopsy", "view_verbalautopsy"],
    },
    "Data Managers": {
        Dashboard: ["view_dashboard", "download_data", "view_pii"],
        User: ["view_user"],
        VerbalAutopsy: ["change_verbalautopsy", "view_verbalautopsy"],
    },
    "Data Viewers": {
        Dashboard: ["view_dashboard"],
        User: [],
        VerbalAutopsy: ["view_verbalautopsy"],
    },
    "Field Workers": {
        Dashboard: ["view_dashboard"],
        User: [],
        VerbalAutopsy: ["view_verbalautopsy"]
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
                for codename in model_permissions:

                    # Get the content type for the given model class.
                    content_type = ContentType.objects.get_for_model(model_class)

                    # Lookup permission based on content type and codename.
                    try:
                        permission = Permission.objects.get(content_type=content_type, codename=codename)
                        group.permissions.add(permission)
                        self.stdout.write(f"Adding {codename} to group {group}")
                    except Permission.DoesNotExist:
                        self.stderr.write(f"{codename} not found")
