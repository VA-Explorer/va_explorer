from io import StringIO
from pathlib import Path

import pandas
import pytest
import datetime
from django.core.management import call_command

from va_explorer.va_data_management.models import Location
from va_explorer.va_data_management.models import VerbalAutopsy

from va_explorer.va_data_management.utils.loading import load_records_from_dataframe

pytestmark = pytest.mark.django_db


def test_loading_from_dataframe():
    # Location gets assigned with field hospital by name or by the user's default location
    # TODO create a test that assigns location by the username
    loc = Location.add_root(name='test location', location_type='facility')

    data = [
        {'instanceid': 'instance1', 'testing-dashes-Id10007': 'name 1', 'Id10023':'03/01/2021', 'hospital': 'test location'},
        {'instanceid': 'instance2', 'testing-dashes-Id10007': 'name 2', 'Id10023': 'dk', 'hospital': 'test location' },
    ]

    df = pandas.DataFrame.from_records(data)

    result = load_records_from_dataframe(df)

    assert len(result['created']) == 2
    assert len(result['ignored']) == 0

    assert result['created'][0].instanceid == data[0]['instanceid']
    assert result['created'][0].Id10007 == data[0]['testing-dashes-Id10007']
    assert result['created'][0].location == loc

    assert result['created'][1].instanceid == data[1]['instanceid']
    assert result['created'][1].Id10007 == data[1]['testing-dashes-Id10007']
    assert result['created'][1].location == loc


def test_loading_from_dataframe_with_ignored():
    # Location gets assigned automatically/randomly.
    # If that changes in loading.py we'll need to change that here too.
    loc = Location.add_root(name='test location', location_type='facility')

    data = [
        {'instanceid': 'instance1', 'testing-dashes-Id10007': 'name 1' },
        {'instanceid': 'instance2', 'testing-dashes-Id10007': 'name 2' },
    ]

    df = pandas.DataFrame.from_records(data)

    result = load_records_from_dataframe(df)

    assert len(result['created']) == 2
    assert len(result['ignored']) == 0
    assert result['created'][0].instanceid == data[0]['instanceid']
    assert result['created'][1].instanceid == data[1]['instanceid']

    # Run it again and it should ignore one of these records.

    data = [
        {'instanceid': 'instance1', 'testing-dashes-Id10007': 'name 1' },
        {'instanceid': 'instance4', 'testing-dashes-Id10007': 'name 4' },
    ]

    df = pandas.DataFrame.from_records(data)

    result = load_records_from_dataframe(df)

    assert len(result['created']) == 1
    assert len(result['ignored']) == 1
    assert result['ignored'][0].instanceid == data[0]['instanceid']
    assert result['created'][0].instanceid == data[1]['instanceid']



def test_loading_from_dataframe_with_key():
    # Location gets assigned automatically/randomly if hospital is not a facility
    # If that changes in loading.py it needs to change here too
    loc = Location.add_root(name='test location', location_type='facility')

    data = [
        {'key': 'instance1', 'testing-dashes-Id10007': 'name 1', 'hospital': 'test location'},
        {'key': 'instance2', 'testing-dashes-Id10007': 'name 2', 'hospital': 'home' },
    ]

    df = pandas.DataFrame.from_records(data)

    result = load_records_from_dataframe(df)

    assert len(result['created']) == 2
    assert len(result['ignored']) == 0

    assert result['created'][0].instanceid == data[0]['key']
    assert result['created'][0].Id10007 == data[0]['testing-dashes-Id10007']
    assert result['created'][0].location == loc

    assert result['created'][1].instanceid == data[1]['key']
    assert result['created'][1].Id10007 == data[1]['testing-dashes-Id10007']
    assert result['created'][1].location.name == 'Unknown'


def test_load_va_csv_command():
    # Location gets assigned automatically/randomly if hospital is not a facility
    # If that changes in loading.py it needs to change here too
    loc = Location.add_root(name='test location', location_type='facility')

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

    assert output.getvalue().strip() == "Loaded 3 verbal autopsies (0 ignored)"
    assert VerbalAutopsy.objects.get(instanceid='instance1').Id10007 == 'name1'
    assert VerbalAutopsy.objects.get(instanceid='instance2').Id10007 == 'name2'
    assert VerbalAutopsy.objects.get(instanceid='instance3').Id10007 == 'name3'

# TODO add tests for date of death, location, and age_group


