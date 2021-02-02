from va_explorer.va_data_management.models import VerbalAutopsy, CauseOfDeath, CauseCodingIssue
from django.forms.models import model_to_dict
from io import StringIO
from collections import OrderedDict
import requests
import csv
import json
import re
import pandas as pd

def run_coding_algorithms():

    # Load all verbal autopsies that don't have a cause coding
    # TODO: This should eventuall check to see that there's a cause coding for every supported algorithm
    verbal_autopsies_without_causes = VerbalAutopsy.objects.filter(causes__isnull=True)

    # Get into CSV format, also prefixing keys with - as expected by pyCrossVA (e.g. Id10424 becomes -Id10424)
    va_data = [model_to_dict(va) for va in verbal_autopsies_without_causes]
    va_data = [dict([(f'-{k}', v) for k, v in d.items()]) for d in va_data]
    va_data_csv = pd.DataFrame.from_records(va_data).to_csv()

    # Call the pyCrossVA translation service and the cause coding service

    # TODO: This will be orchestrated using docker; if needed stand up manually using these instructions:
    # https://github.com/VA-Explorer/pyCrossVA/tree/microservice-experiment
    # https://github.com/VA-Explorer/InterVA5/tree/microservice-experiment

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
    algorithm_response_data = json.loads(algorithm_response.text)

    # Populate the database!
    # TODO: currently some VAs don't process at all, and some of those that process don't get a cause
    # of death assigned; we need to be able to track and report on this type of error
    # TODO: at the moment we ignore some data from the algorithm (cause2, cause3, comcat, lik2, etc)
    causes = []
    for cause_data in algorithm_response_data['results']['VA5']:
        cause = cause_data['CAUSE1'][0].strip()
        if cause:
            # TODO: confirm: the IDs that come back appear to be offsets into the supplied data and don't reflect the ID sent
            va_offset = int(cause_data['ID'][0].strip())
            va_id = verbal_autopsies_without_causes[va_offset].id
            causes.append(CauseOfDeath(verbalautopsy_id=va_id, cause=cause, algorithm='InterVA5', settings=algorithm_settings))

    CauseOfDeath.objects.bulk_create(causes)

    issues = []
    for severity in CauseCodingIssue.SEVERITY_OPTIONS:
        for issue in algorithm_response_data[severity + 's']:
            # TODO: confirm: the IDs that come back appear to be offsets into the supplied data and don't reflect the ID sent
            # TODO: return data should not require parsing this way, add more structure
            if isinstance(issue, list):
                issue = issue[0]
            va_offset, *issue_text = re.split('  +', issue)
            issue_text = ' '.join(issue_text).strip()
            va_id = verbal_autopsies_without_causes[int(va_offset)].id
            # TODO: For now, clear old issues for records that are newly coded; if we associate errors with runs we may perhaps prefer not to do this
            CauseCodingIssue.objects.filter(verbalautopsy_id=va_id).delete()
            issues.append(CauseCodingIssue(verbalautopsy_id=va_id, text=issue_text, severity=severity, algorithm='InterVA5', settings=algorithm_settings))

    CauseCodingIssue.objects.bulk_create(issues)

    return dict(count=len(algorithm_input_rows), coded_count=len(causes), issue_count=len(issues))
