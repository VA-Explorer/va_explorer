from io import StringIO
from pathlib import Path

import pandas
import pytest
from django.core.management import call_command

from va_explorer.tests.factories import VerbalAutopsyFactory
from va_explorer.va_data_management.models import Location, VerbalAutopsy
from va_explorer.va_data_management.utils.loading import load_records_from_dataframe

pytestmark = pytest.mark.django_db


def test_loading_from_dataframe():
    # Location gets assigned w/ field hospital by name or by user's default location
    loc = Location.add_root(
        name="Test Location", key="test_location", location_type="facility"
    )

    data = [
        {
            "instanceid": "instance1",
            "Id10017": "name",
            "Id10018": "1",
            "Id10012": "2021-03-21",
            "instancename": "_Dec---name 1---2021-03-21",
            "testing-dashes-Id10007": "name 1",
            "Id10023": "03/01/2021",
            "hospital": "test_location",
        },
        {
            "instanceid": "instance2",
            "Id10017": "name",
            "Id10018": "2",
            "Id10012": "2021-03-22",
            "instancename": "_Dec---name 2---2021-03-22",
            "testing-dashes-Id10007": "name 2",
            "Id10023": "dk",
            "hospital": "test_location",
        },
    ]

    df = pandas.DataFrame.from_records(data)

    result = load_records_from_dataframe(df)

    assert len(result["created"]) == 2
    assert len(result["ignored"]) == 0

    assert result["created"][0].instanceid == data[0]["instanceid"]
    assert result["created"][0].Id10007 == data[0]["testing-dashes-Id10007"]
    assert result["created"][0].location == loc

    assert result["created"][1].instanceid == data[1]["instanceid"]
    assert result["created"][1].Id10007 == data[1]["testing-dashes-Id10007"]
    assert result["created"][1].location == loc


def test_loading_from_dataframe_with_ignored():
    # Location gets assigned automatically/randomly.
    # If that changes in loading.py we'll need to change that here too.
    Location.add_root(
        name="Test Location", key="test_location", location_type="facility"
    )

    data = [
        {
            "instanceid": "instance1",
            "Id10017": "name",
            "Id10018": "1",
            "Id10012": "2021-03-21",
            "testing-dashes-Id10007": "name 1",
            "instancename": "_Dec---name 1---2021-03-21",
        },
        {
            "instanceid": "instance2",
            "Id10017": "name",
            "Id10018": "2",
            "Id10012": "2021-03-22",
            "testing-dashes-Id10007": "name 2",
            "instancename": "_Dec---name 2---2021-03-22",
        },
    ]

    df = pandas.DataFrame.from_records(data)

    result = load_records_from_dataframe(df)

    assert len(result["created"]) == 2
    assert len(result["ignored"]) == 0
    assert result["created"][0].instanceid == data[0]["instanceid"]
    assert result["created"][1].instanceid == data[1]["instanceid"]

    # Run it again and it should ignore one of these records.

    data = [
        {
            "instanceid": "instance1",
            "Id10017": "name",
            "Id10018": "1",
            "Id10012": "2021-03-21",
            "testing-dashes-Id10007": "name 1",
            "instancename": "_Dec---name 1---2021-03-21",
        },
        {
            "instanceid": "instance4",
            "Id10017": "name",
            "Id10018": "4",
            "Id10012": "2021-03-24",
            "testing-dashes-Id10007": "name 4",
            "instancename": "_Dec---name 4---2021-03-24",
        },
    ]

    df = pandas.DataFrame.from_records(data)

    result = load_records_from_dataframe(df)

    assert len(result["created"]) == 1
    assert len(result["ignored"]) == 1
    assert result["ignored"][0].instanceid == data[0]["instanceid"]
    assert result["created"][0].instanceid == data[1]["instanceid"]


def test_loading_from_dataframe_with_key():
    # Location gets assigned automatically/randomly if hospital is not a facility
    # If that changes in loading.py it needs to change here too
    loc = Location.add_root(
        name="Test Location", key="test_location", location_type="facility"
    )

    data = [
        {
            "key": "instance1",
            "Id10017": "name",
            "Id10018": "1",
            "Id10012": "2021-03-21",
            "instancename": "_Dec---name 1---2021-03-21",
            "testing-dashes-Id10007": "name 1",
            "hospital": "test_location",
        },
        {
            "key": "instance2",
            "Id10017": "name",
            "Id10018": "2",
            "Id10012": "2021-03-22",
            "testing-dashes-Id10007": "name 2",
            "instancename": "_Dec---name 2---2021-03-22",
            "hospital": "home",
        },
    ]

    df = pandas.DataFrame.from_records(data)

    result = load_records_from_dataframe(df)

    assert len(result["created"]) == 2
    assert len(result["ignored"]) == 0

    assert result["created"][0].instanceid == data[0]["key"]
    assert result["created"][0].Id10007 == data[0]["testing-dashes-Id10007"]
    assert result["created"][0].location == loc

    assert result["created"][1].instanceid == data[1]["key"]
    assert result["created"][1].Id10007 == data[1]["testing-dashes-Id10007"]
    assert result["created"][1].location.name == "Unknown"


def test_load_va_csv_command():
    # Location gets assigned automatically/randomly if hospital is not a facility
    # If that changes in loading.py it needs to change here too
    Location.add_root(
        name="Test Location", key="test_location", location_type="facility"
    )

    # Find path to data file
    test_data = Path(__file__).parent / "test-input-data.csv"

    assert VerbalAutopsy.objects.count() == 0

    output = StringIO()
    call_command(
        "load_va_csv",
        str(test_data.absolute()),
        stdout=output,
        stderr=output,
    )

    assert (
        output.getvalue().strip() == "Loaded 3 verbal autopsies from CSV "
        "(0 ignored, 0 removed as outdated)"
    )
    assert VerbalAutopsy.objects.get(instanceid="instance1").Id10007 == "name1"
    assert VerbalAutopsy.objects.get(instanceid="instance2").Id10007 == "name2"
    assert VerbalAutopsy.objects.get(instanceid="instance3").Id10007 == "name3"


def test_loading_duplicate_vas(settings):
    settings.QUESTIONS_TO_AUTODETECT_DUPLICATES = (
        "Id10017, Id10018, Id10012, Id10019, Id10020, Id10021, Id10022, Id10023"
    )

    # va1 matches 2 records in 'test-duplicate-input-data.csv'
    # VA will not be marked as duplicate = True because it was created before loading
    # 'test-duplicate-input-data.csv'
    va1 = VerbalAutopsyFactory.create(
        Id10017="Bob",
        Id10018="Jones",
        Id10012="2021-03-22",
        Id10019="Male",
        Id10020="Yes",
        Id10021="dk",
        Id10022="Yes",
        Id10023="dk",
        instanceid="00",
        instancename="_Dec---Bob_Jones---2021-03-22",
    )

    # va2 matches 0 records in 'test-duplicate-input-data.csv'
    va2 = VerbalAutopsyFactory.create(
        Id10017="Nate",
        Id10018="Grey",
        Id10012="2012-03-22",
        Id10019="Male",
        Id10020="Yes",
        Id10021="dk",
        Id10022="Yes",
        Id10023="dk",
        instanceid="02",
        instancename="_Dec---Nate_Grey---2021-03-22",
    )

    # Find path to data file
    test_data = Path(__file__).parent / "test-duplicate-input-data.csv"

    output = StringIO()
    call_command(
        "load_va_csv",
        str(test_data.absolute()),
        stdout=output,
        stderr=output,
    )

    va1.refresh_from_db()
    va2.refresh_from_db()

    assert not va1.duplicate
    assert not va2.duplicate

    # Query for the VAs that match va1
    vas_duplicate_with_va1 = list(
        VerbalAutopsy.objects.filter(
            unique_va_identifier=va1.unique_va_identifier
        ).order_by("created")
    )

    assert len(vas_duplicate_with_va1) == 3

    # Assert that the oldest VA by created timestamp is not duplicate
    assert not vas_duplicate_with_va1.pop(0).duplicate

    # Assert that the rest are duplicate
    for va in vas_duplicate_with_va1:
        assert va.duplicate

    assert (
        VerbalAutopsy.objects.filter(
            unique_va_identifier=va2.unique_va_identifier
        ).count()
        == 1
    )


# TODO add tests for date of death, location, and age_group
