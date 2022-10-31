from django.db import models


# Adds a model that is not backed by a table in the database
class Dashboard(models.Model):
    class Meta:
        managed = False

        # disable "add", "change", "delete"
        # comma here necessary
        default_permissions = ("view",)

        permissions = (
            ("download_data", "Can download data"),
            ("view_pii", "Can view PII in data"),
            ("supervise_users", "Can supervise other users"),
        )
