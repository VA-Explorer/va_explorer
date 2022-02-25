from django.core.management.base import BaseCommand
from va_explorer.va_data_management.models import Location
from va_explorer.va_data_management.utils.loading import load_locations_from_file
import argparse
import pandas as pd

class Command(BaseCommand):

    # TODO: Need an approach that supports loading of country-specfic location information

    help = 'Loads initial location data into the database from a CSV file with Name, Type, and Parent columns'

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=argparse.FileType('r'))
        parser.add_argument('--delete_previous', type=bool, nargs='?', default=False)

    def handle(self, *args, **options):

        # Load the CSV file
        csv_file = options['csv_file']
        delete_previous = options['delete_previous']

        # see loading.py in va_data_management_utils for implementation
        load_locations_from_file(csv_file, delete_previous=delete_previous)

