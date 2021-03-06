from os import environ
from django.core.management.base import BaseCommand
from va_explorer.va_data_management.models import VerbalAutopsy
from random import randint
from math import sqrt, ceil
from datetime import date, timedelta

# Demo only: script to ramdomize VA dates for demos of e.g. the metrics page

class Command(BaseCommand):

    help = "Randomize dates for demos, to be run only in development mode"

    def handle(self, *args, **options):

        if not environ.get("DJANGO_SETTINGS_MODULE") == "config.settings.local":
            message = "This functionality is for demo purposes only in the local environment. Exiting."
            self.stdout.write(self.style.ERROR(message))
            exit()

        # Randomize the dates for all VAs in the system so that they take place over
        # the past ~6 months at (randomness willing) an increasing rate; we want them
        # to be in the database in increasing date order so we first create a batch of
        # dates then assign them
        count = VerbalAutopsy.objects.count()
        days_list = [183 - ceil(sqrt(randint(1, 183 ** 2))) for _ in range(count)]
        dates_list = [date.today() - timedelta(days=days) for days in days_list]
        dates_list.sort()
        for va, new_date in zip(VerbalAutopsy.objects.all(), dates_list):
            # Set Id10023 and created and updated all to same date
            va.Id10023 = va.created = va.updated = new_date
            va.save()
