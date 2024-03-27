import sys
from math import ceil, sqrt
from os import environ
from random import randint

import pytz
from django.core.management.base import BaseCommand
from django.utils import timezone
from tqdm import tqdm

from va_explorer.va_data_management.models import VerbalAutopsy

# Demo only: script to randomize VA dates for demos of e.g. the metrics page


class Command(BaseCommand):
    help = "Randomize dates for demos, to be run only in development mode"

    def handle(self, *args, **options):
        if environ.get("DJANGO_SETTINGS_MODULE") != "config.settings.local":
            message = "This functionality is for demo purposes only (local env) Exiting"
            self.stdout.write(self.style.ERROR(message))
            sys.exit()

        # Randomize the dates for all VAs in the system so that they take place over
        # the past ~6 months at (randomness willing) an increasing rate; we want them
        # to be in the database in increasing date order so we first create a batch of
        # dates then assign them
        count = VerbalAutopsy.objects.count()
        days_list = [183 - ceil(sqrt(randint(1, 183**2))) for _ in range(count)]
        dates_list = []
        for days in days_list:
            date = timezone.now() - timezone.timedelta(days=days)
            if timezone.is_naive(date):
                date = timezone.make_aware()
                date = date.astimezone(pytz.utc)
            dates_list.append(date)

        dates_list.sort()
        for va, new_date in tqdm(
            zip(VerbalAutopsy.objects.all(), dates_list, strict=True), total=count
        ):
            # Set Id10023 and created and updated all to same date
            va.Id10023 = va.created = va.updated = va.Id10012 = new_date
            va.skip_history_when_saving = True
            va.save()
