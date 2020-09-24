from django.core.management.base import BaseCommand
from verbal_autopsy.models import VerbalAutopsy, Location
import argparse
import pandas as pd
import re

class Command(BaseCommand):

    help = 'Loads a verbal autopsy CSV file into the database'

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=argparse.FileType('r'))

    def handle(self, *args, **options):

        # Load the CSV file
        csv_data = pd.read_csv(options['csv_file'])

        # CSV can prefix column names with a dash or more, remove everything up to and including last dash
        csv_data.rename(columns=lambda c: re.sub('^.*-', '', c), inplace=True)

        # Figure out the common field names across the CSV and our model
        model_field_names = pd.Index([f.name for f in VerbalAutopsy._meta.get_fields()])
        
        # But first, account for case differences in csv columns (i.e. ensure id10041 maps to Id10041)
        fieldCaseMapper = {field.lower(): field for field in model_field_names} 
        csv_data.rename(columns=lambda c: fieldCaseMapper.get(c.lower(), c), inplace=True)

        csv_field_names = csv_data.columns
        common_field_names = csv_field_names.intersection(model_field_names)

        # Just keep the fields in the CSV that we have columns for in our VerbalAutopsy model
        # Also track extras or missing fields for eventual debugging display
        missing_field_names = model_field_names.difference(common_field_names)
        extra_field_names = csv_field_names.difference(common_field_names)
        csv_data = csv_data[common_field_names]

        # Populate the database!
        verbal_autopsies = [VerbalAutopsy(**row) for row in csv_data.to_dict(orient='records')]
        # TODO: For now treat this as synthetic data and randomly assign a facility as the location
        for va in verbal_autopsies:
            va.location = Location.objects.filter(location_type='facility').order_by('?').first()
        VerbalAutopsy.objects.bulk_create(verbal_autopsies)

        self.stdout.write(f'Loaded {len(verbal_autopsies)} verbal autopsies')
