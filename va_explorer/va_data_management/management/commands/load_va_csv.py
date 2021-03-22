import argparse

import pandas as pd
from django.core.management.base import BaseCommand
from simple_history.utils import bulk_create_with_history

from va_explorer.va_data_management.utils.loading import load_records_from_dataframe


class Command(BaseCommand):

    help = 'Loads a verbal autopsy CSV file into the database'

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=argparse.FileType('r'))

    def handle(self, *args, **options):
        csv_data = pd.read_csv(options['csv_file'])

        results = load_records_from_dataframe(csv_data)

        num_total = len(results['verbal_autopsies'])

        self.stdout.write(f'Loaded {num_total} verbal autopsies')
