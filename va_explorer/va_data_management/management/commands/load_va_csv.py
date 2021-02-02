from django.core.management.base import BaseCommand
from va_explorer.utils.data_import import load_records_from_dataframe  
import argparse
import pandas as pd

class Command(BaseCommand):

    help = 'Loads a verbal autopsy CSV file into the database'

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=argparse.FileType('r'))

    def handle(self, *args, **options):

        # Load the CSV file
        csv_data = pd.read_csv(options['csv_file'])
        
        load_records_from_dataframe(csv_data)
