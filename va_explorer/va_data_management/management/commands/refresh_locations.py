from django.conf import settings
from django.core.management.base import BaseCommand

from va_explorer.va_data_management.models import Location, VerbalAutopsy
from va_explorer.va_data_management.utils.location_assignment import assign_va_location
from va_explorer.va_data_management.utils.validate import validate_vas_for_dashboard


class Command(BaseCommand):
    help = "Reassigns locations based on most recent facility list"

    def handle(self, *args, **options):
        if settings.DEBUG:
            count = VerbalAutopsy.objects.count()
            print(
                "Refreshing locations for all " + str(count) + " VAs in the database."
            )

        # build location mapper to map csv locations to known db locations
        # using list comprehension to remove duplicated from list
        location_map = {}
        verbal_autopsies = list(VerbalAutopsy.objects.all())
        h = [va.hospital for va in verbal_autopsies]
        hospitals = []
        [hospitals.append(x) for x in h if x not in hospitals]

        location_map = {
            key_name_pair[0]: key_name_pair[1]
            for key_name_pair in Location.objects.filter(key__in=hospitals)
            .only("name", "key")
            .values_list("key", "name")
        }

        changed_count = 0
        for va in verbal_autopsies:
            old_location = va.location
            new_va = assign_va_location(va, location_map)
            new_location = new_va.location

            if old_location != new_location:
                changed_count += 1
                va.location = new_va.location
                va.save_without_historical_record()

        validate_vas_for_dashboard(verbal_autopsies)

        print("   changed locations for " + str(changed_count) + " VA(s).")
