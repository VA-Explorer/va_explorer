from django.core.management.base import BaseCommand
from verbal_autopsy.models import VerbalAutopsy, CauseOfDeath
from django.forms.models import model_to_dict
from io import StringIO
from collections import OrderedDict
import requests
import csv
import json
import pandas as pd

# TODO: Temporary script to run COD assignment algorithms; this should
# eventually become something that's handle with celery

class Command(BaseCommand):

    help = 'Run cause coding algorithms'

    def handle(self, *args, **options):

        # Load all verbal autopsies that don't have a cause coding
        # TODO: This should eventuall check to see that there's a cause coding for every supported algorithm
        verbal_autopsies_without_causes = VerbalAutopsy.objects.filter(causes__isnull=True)

        # Get into CSV format, also prefixing keys with - as expected by pyCrossVA (e.g. Id10424 becomes -Id10424)
        va_data = [model_to_dict(va) for va in verbal_autopsies_without_causes]
        va_data = [dict([(f'-{k}', v) for k, v in d.items()]) for d in va_data]
        va_data_csv = pd.DataFrame.from_records(va_data).to_csv()

        # Call the pyCrossVA translation service and the cause coding service

        # TODO: This will be orchestrated using docker; until then stand up manually using these instructions:
        # https://github.com/pkmitre/pyCrossVA/tree/microservice-experiment
        # https://github.com/pkmitre/InterVA5/tree/microservice-experiment

        # Transform to algorithm format using the pyCrossVA web service
        transform_url = 'http://127.0.0.1:5001/transform?input=2016WHOv151&output=InterVA5'
        transform_response = requests.post(transform_url, data=va_data_csv)

        # We need to convert the resulting CSV to JSON
        # TODO: settings need to be configurable
        algorithm_settings = { 'HIV': 'l', 'Malaria': 'l' }
        # TODO: should this use pandas?
        transform_response_reader = csv.DictReader(StringIO(transform_response.text))
        algorithm_input_rows = []
        for row in transform_response_reader:
            # Replace blank key with ID and append to list for later jsonification
            algorithm_input_rows.append(OrderedDict([('ID', v) if k == '' else (k, v) for k, v in row.items()]))
        algorithm_input_json = json.dumps({ 'Input': algorithm_input_rows, **algorithm_settings })
        # TODO: Temporary hack to get to the required algorithm format
        algorithm_input_json = algorithm_input_json.replace('"0.0"', '"."').replace('"1.0"', '"y"')

        # Send to InterVA algorithm web service
        algorithm_url = 'http://127.0.0.1:5002/interva5'
        algorithm_response = requests.post(algorithm_url, data=algorithm_input_json)

        # Populate the database!
        # TODO: currently some VAs don't process at all, and some of those that process don't get a cause
        # of death assigned; we need to be able to track and report on this type of error
        # TODO: at the moment we ignore some data from the algorithm (cause2, cause3, comcat, lik2, etc)
        # TODO: temporary approach for saving causes, aligning to VA data by ID
        # TODO: this use of ID is not likely to be correct, it doesn't actually track back to the real VA ID
        causes = []
        for cause_data in json.loads(algorithm_response.text)['VA5']:
            cause = cause_data['CAUSE1'][0].strip()
            va_id = cause_data['ID'][0].strip()
            if cause:
                causes.append(CauseOfDeath(verbalautopsy_id=va_id, cause=cause, algorithm='InterVA5', settings=algorithm_settings))

        CauseOfDeath.objects.bulk_create(causes)

        self.stdout.write(f'Coded {len(causes)} verbal autopsies (out of {len(algorithm_input_rows)})')
