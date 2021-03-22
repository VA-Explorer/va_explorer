import os

import pandas as pd
from django.core.management.base import BaseCommand

from va_explorer.va_data_management.utils.loading import load_records_from_dataframe
from va_explorer.va_data_management.utils.odk import download_responses


class Command(BaseCommand):
    help = 'Loads a verbal autopsy data from ODK into the database'

    def add_arguments(self, parser):
        parser.add_argument('--email', type=str, required=False, default=os.environ.get('ODK_EMAIL'))
        parser.add_argument('--password', type=str, required=False, default=os.environ.get('ODK_PASSWORD'))
        parser.add_argument('--project-name', type=str, required=False)
        parser.add_argument('--project-id', type=str, required=False)

    def handle(self, *args, **options):
        email = options['email']
        password = options['password']
        project_id = options['project_id']
        project_name = options['project_name']

        if not email or not password:
            raise ValueError('Must specify either --email and --password arguments or ODK_EMAIL and ODK_PASSWORD environment variables.')

        if not project_id and not project_name:
            raise ValueError('Must specify either --project-id or --project-name arguments.')

        forms = download_responses(email, password, project_name, project_id)

        results = load_records_from_dataframe(forms)

        num_total = len(results['verbal_autopsies'])

        self.stdout.write(f'Loaded {num_total} verbal autopsies from ODK')
