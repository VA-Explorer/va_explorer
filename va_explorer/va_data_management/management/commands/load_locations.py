from django.core.management.base import BaseCommand
from va_explorer.va_data_management.models import Location
import argparse
import pandas as pd

class Command(BaseCommand):

    # TODO: Need an approach that supports loading of country-specfic location information

    help = 'Loads initial location data into the database from a CSV file with Name, Type, and Parent columns'

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=argparse.FileType('r'))

    def handle(self, *args, **options):

        # Load the CSV file
        csv_data = pd.read_csv(options['csv_file'], keep_default_na=False)

        # Clear out any existing locations (this is for initialization only)
        Location.objects.all().delete()

        # Store it into the database in a tree structure
        for row in csv_data.itertuples():
            if row.Parent:
                self.stdout.write(f'Adding {row.Name} as child node of {row.Parent}')
                parent_node = Location.objects.get(name=row.Parent)
                parent_node.add_child(name=row.Name, location_type=row.Type)
            else:
                self.stdout.write(f'Adding root node for {row.Name}')
                Location.add_root(name=row.Name, location_type=row.Type)
