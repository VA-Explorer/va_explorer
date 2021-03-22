from io import StringIO
from pathlib import Path

import pandas
import pytest
from django.core.management import call_command

from va_explorer.va_data_management.models import Location
from va_explorer.va_data_management.models import VerbalAutopsy
from va_explorer.va_data_management.utils.loading import load_records_from_dataframe

pytestmark = pytest.mark.django_db


def test_loading_from_dataframe():
    # Location gets assigned automatically/randomly.
    # If that changes in loading.py we'll need to change that here too.
    loc = Location.objects.create(name='test location', location_type='facility', depth=0, numchild=0, path='0001')

    data = [
        {'instanceid': 'instance1', 'testing-dashes-Id10007': 'name 1' },
        {'instanceid': 'instance2', 'testing-dashes-Id10007': 'name 2' },
    ]

    df = pandas.DataFrame.from_records(data)

    result = load_records_from_dataframe(df)

    assert len(result['verbal_autopsies']) == 2

    assert result['verbal_autopsies'][0].instanceid == data[0]['instanceid']
    assert result['verbal_autopsies'][0].Id10007 == data[0]['testing-dashes-Id10007']
    assert result['verbal_autopsies'][0].location == loc

    assert result['verbal_autopsies'][1].instanceid == data[1]['instanceid']
    assert result['verbal_autopsies'][1].Id10007 == data[1]['testing-dashes-Id10007']
    assert result['verbal_autopsies'][1].location == loc



def test_loading_from_dataframe_with_key():
    # Location gets assigned automatically/randomly.
    # If that changes in loading.py we'll need to change that here too.
    loc = Location.objects.create(name='test location', location_type='facility', depth=0, numchild=0, path='0001')

    data = [
        {'key': 'instance1', 'testing-dashes-Id10007': 'name 1' },
        {'key': 'instance2', 'testing-dashes-Id10007': 'name 2' },
    ]

    df = pandas.DataFrame.from_records(data)

    result = load_records_from_dataframe(df)

    assert len(result['verbal_autopsies']) == 2

    assert result['verbal_autopsies'][0].instanceid == data[0]['key']
    assert result['verbal_autopsies'][0].Id10007 == data[0]['testing-dashes-Id10007']
    assert result['verbal_autopsies'][0].location == loc

    assert result['verbal_autopsies'][1].instanceid == data[1]['key']
    assert result['verbal_autopsies'][1].Id10007 == data[1]['testing-dashes-Id10007']
    assert result['verbal_autopsies'][1].location == loc


def test_load_va_csv_command():
    # Location gets assigned automatically/randomly.
    # If that changes in loading.py we'll need to change that here too.
    Location.objects.create(name='test location', location_type='facility', depth=0, numchild=0, path='0001')

    # Find path to data file
    test_data = Path(__file__).parent / 'test-input-data.csv'

    assert VerbalAutopsy.objects.count() == 0

    output = StringIO()

    call_command(
        "load_va_csv", 
        str(test_data.absolute()), 
        stdout=output,
        stderr=output,
    )

    assert output.getvalue().startswith("Loaded 3 verbal autopsies")
    assert VerbalAutopsy.objects.get(instanceid='instance1').Id10007 == 'name1'
    assert VerbalAutopsy.objects.get(instanceid='instance2').Id10007 == 'name2'
    assert VerbalAutopsy.objects.get(instanceid='instance3').Id10007 == 'name3'
