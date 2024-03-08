import argparse

import pandas as pd
from django.core.management.base import BaseCommand

from va_explorer.va_data_management.models import Location, VerbalAutopsy
from va_explorer.va_data_management.utils.location_assignment import assign_va_location
from va_explorer.va_data_management.utils.validate import validate_vas_for_dashboard


class Command(BaseCommand):
    help = "Reassigns locations based on most recent facility list"

    # def add_arguments(self, parser):
    #     # parser.add_argument("csv_file", type=argparse.FileType("r"))
    #     # parser.add_argument("--random_locations", type=str, nargs="?", default=False)

    def handle(self, *args, **options):

        # verbal_autopsies = VerbalAutopsy.objects
        count = VerbalAutopsy.objects.count()
        print("Refreshing locations for all " + str(count) + " VAs in the database.")

        location_map = {}

        verbal_autopsies = list(
           VerbalAutopsy.objects.filter()[0:count]
        )

        # build location mapper to map csv locations to known db locations
        h = [va.hospital for va in verbal_autopsies]
        # using list comprehension to remove duplicated from list
        hospitals = []
        [hospitals.append(x) for x in h if x not in hospitals]

        location_map = {
                key_name_pair[0]: key_name_pair[1]
                for key_name_pair in Location.objects.filter(key__in=hospitals)
                .only("name", "key")
                .values_list("key", "name")
            }    
        
        changedcount = 0

        for va in verbal_autopsies:
            oldlocation = va.location
            newva = assign_va_location(va, location_map)
            newlocation = newva.location
            
            if oldlocation != newlocation:
                changedcount += 1
                va.location = newva.location
                va.save_without_historical_record()
                validate_vas_for_dashboard(va)


        print("   changed locations for " + str(changedcount) + " VA(s).")
