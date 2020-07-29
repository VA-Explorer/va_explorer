from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.core.management import BaseCommand

User = get_user_model()

GROUPS_PERMISSIONS = {
    "Admins": {User: ["add", "change", "delete", "view"]},
    "Data Managers": {User: ["add", "change", "delete", "view"]},
    "Data Viewers": {User: ["view"]},
    "Field Workers": {User: []},
}


class Command(BaseCommand):
    def __init__(self, *args, **kwargs):
        super(Command, self).__init__(*args, **kwargs)

    help = "Create default groups"

    def handle(self, *args, **options):
        # Loop through groups and permissions; add permissions, as applicable, to related group objects
        for group_name, group_permissions in GROUPS_PERMISSIONS.items():
            group, created = Group.objects.get_or_create(name=group_name)

            for model_class, model_permissions in group_permissions.items():
                for model_permission_name in model_permissions:

                    # Generate permission name as Django would, in terms of format
                    codename = f"{model_permission_name}_{model_class._meta.model_name}"

                    try:
                        permission = Permission.objects.get(codename=codename)
                        group.permissions.add(permission)
                        self.stdout.write(f"Adding {codename} to group {group}")
                    except Permission.DoesNotExist:
                        self.stdout.write(f"{codename} not found")
