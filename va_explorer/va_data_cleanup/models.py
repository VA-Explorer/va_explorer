from django.db import models


# Adds a model that is not backed by a table in the database
class DataCleanup(models.Model):
    class Meta:
        managed = False

        # disable "add", "change", "delete"
        # comma here necessary
        default_permissions = ("view",)

        permissions = (
            ("download", "Can download"),
            ("bulk_download", "Can bulk download"),
        )
