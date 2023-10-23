from datetime import date, datetime
from os import environ

from django.core.management.base import BaseCommand

from va_explorer.va_data_management.models import VerbalAutopsy

# Demo only: script to update all VA dates in the system to allow an
# older data set to be used for demonstration purposes


class Command(BaseCommand):
    help = "Update dates for demos to make the loaded VAs look current, to be \
            run only in development mode"

    def handle(self, *args, **options):
        _ = (args, options)  # unused
        if environ.get("DJANGO_SETTINGS_MODULE") != "config.settings.local":
            message = "This functionality is for demo purposes only in the \
                       local environment. Exiting."
            self.stdout.write(self.style.ERROR(message))
            exit()

        # Find most recent date in system as our baseline, looking at death date only
        # TODO: The date fields should really be stored as dates in the database,
        #       his fails on different string formats for dates
        # TODO: We need a clear picture of all the date fields in the system
        most_recent = max(
            [
                datetime.strptime(date, "%m/%d/%y").date()
                for date in VerbalAutopsy.objects.values_list("Id10023", flat=True)
            ]
        )
        shift = date.today() - most_recent
        for va in VerbalAutopsy.objects.all():
            # Set Id10023 and created and updated all to same date
            va.Id10023 = va.created = va.updated = (
                datetime.strptime(va.Id10023, "%m/%d/%y").date() + shift
            )
            va.save_without_historical_record()
