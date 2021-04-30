import csv
import json
import os
import re
from io import StringIO

import pandas as pd
import requests
from django.forms import model_to_dict

from va_explorer.va_data_management.models import CauseCodingIssue
from va_explorer.va_data_management.models import CauseOfDeath
from va_explorer.va_data_management.models import VerbalAutopsy


PYCROSS_HOST = os.environ.get('PYCROSS_HOST', 'http://127.0.0.1:5001')
INTERVA_HOST = os.environ.get('INTERVA_HOST', 'http://127.0.0.1:5002')

# TODO: settings need to be configurable
ALGORITHM_SETTINGS = {'HIV': 'l', 'Malaria': 'l'}


def _run_pycross_and_interva5(verbal_autopsies):
    # Get into CSV format, also prefixing keys with - as expected by pyCrossVA (e.g. Id10424 becomes -Id10424)
    va_data = [model_to_dict(va) for va in verbal_autopsies]
    va_data = [dict([(f'-{k}', v) for k, v in d.items()]) for d in va_data]
    va_data_csv = pd.DataFrame.from_records(va_data).to_csv()

    # Transform to algorithm format using the pyCrossVA web service
    transform_url = f'{PYCROSS_HOST}/transform?input=2016WHOv151&output=InterVA5'
    transform_response = requests.post(transform_url, data=va_data_csv.encode('utf-8'))

    # Convert result to JSON
    transform_response_reader = csv.DictReader(StringIO(transform_response.text))

    # Replace blank key with ID and append to list for later jsonification
    rows = [
        {'ID' if key == '' else key: value for key, value in row.items()} for row in transform_response_reader
    ]
    result_json = json.dumps({'Input': rows, **ALGORITHM_SETTINGS})

    # This is to get to the data into required algorithm format for interva5
    result_json = result_json.replace('"0.0"', '"."').replace('"1.0"', '"y"')

    algorithm_url = f'{INTERVA_HOST}/interva5'
    algorithm_response = requests.post(algorithm_url, data=result_json)
    return json.loads(algorithm_response.text)


def run_coding_algorithms():
    # Load all verbal autopsies that don't have a cause coding
    # TODO: This should eventually check to see that there's a cause coding for every supported algorithm
    verbal_autopsies_without_causes = list(VerbalAutopsy.objects.filter(causes__isnull=True))

    interva_response_data = _run_pycross_and_interva5(verbal_autopsies_without_causes)

    # The ID that comes back is the index in the data that was passed in.
    # Use that to look up the matching VA in the verbal_autopsies_without_causes list.
    causes = []
    for cause_data in interva_response_data['results']['VA5']:
        cause = cause_data['CAUSE1'][0].strip()
        if cause:
            va_offset = int(cause_data['ID'][0].strip())
            va_id = verbal_autopsies_without_causes[va_offset].id
            causes.append(CauseOfDeath(verbalautopsy_id=va_id, cause=cause, algorithm='InterVA5', settings=ALGORITHM_SETTINGS))
    CauseOfDeath.objects.bulk_create(causes)

    # The ID that comes back is the index in the data that was passed in.
    # Use that to look up the matching VA in the verbal_autopsies_without_causes list.
    issues = []
    for severity in CauseCodingIssue.SEVERITY_OPTIONS:
        for issue in interva_response_data[severity + 's']:
            if isinstance(issue, list):
                issue = issue[0]
            va_offset, issue_text = re.split('  +', issue,  maxsplit=1)
            va_id = verbal_autopsies_without_causes[int(va_offset)].id
            # TODO: For now, clear old issues for records that are newly coded; if we associate errors with runs we may perhaps prefer not to do this
            # use exclude to keep errors related to the raw data
            # TODO: build out the issue model to capture non coding errors
            CauseCodingIssue.objects.filter(verbalautopsy_id=va_id).exclude(algorithm='').delete()
            issues.append(CauseCodingIssue(verbalautopsy_id=va_id, text=issue_text, severity=severity, algorithm='InterVA5', settings=ALGORITHM_SETTINGS))
    CauseCodingIssue.objects.bulk_create(issues)


    return {
        'verbal_autopsies': verbal_autopsies_without_causes,
        'causes': causes,
        'issues': issue,
    }

