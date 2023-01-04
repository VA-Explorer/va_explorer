from io import StringIO

import pytest
from django.core.management import call_command

from va_explorer.tests.factories import VerbalAutopsyFactory

pytestmark = pytest.mark.django_db


def test_mark_vas_as_duplicate_with_empty_configuration(settings):
    settings.QUESTIONS_TO_AUTODETECT_DUPLICATES = None

    output = StringIO()
    with pytest.raises(SystemExit) as _:
        call_command("mark_vas_as_duplicate", stdout=output, stderr=output)

    assert (
        output.getvalue().strip()
        == "Error: Configuration, QUESTIONS_TO_AUTODETECT_DUPLICATES, is an "
        "empty list.\n Please update your .env file with a list of questions "
        "by Id that will be used to autodetect duplicates."
    )


def test_mark_vas_as_duplicate(settings):
    settings.QUESTIONS_TO_AUTODETECT_DUPLICATES = None

    # Create some VAs, mimicking the setting where
    # QUESTIONS_TO_AUTODETECT_DUPLICATES is None
    va1 = VerbalAutopsyFactory.create(
        Id10017="Bob",
        Id10018="Jones",
        Id10019="Male",
        Id10020="Yes",
        Id10021="dk",
        Id10022="Yes",
        Id10023="dk",
        instanceid="00",
    )

    duplicate_of_va1 = VerbalAutopsyFactory.create(
        Id10017="Bob",
        Id10018="Jones",
        Id10019="Male",
        Id10020="Yes",
        Id10021="dk",
        Id10022="Yes",
        Id10023="dk",
        instanceid="00",
    )

    va2 = VerbalAutopsyFactory.create(
        Id10017="Nate",
        Id10018="Grey",
        Id10019="Male",
        Id10020="Yes",
        Id10021="dk",
        Id10022="Yes",
        Id10023="dk",
        instanceid="02",
    )

    duplicate_of_va2 = VerbalAutopsyFactory.create(
        Id10017="Nate",
        Id10018="Grey",
        Id10019="Male",
        Id10020="Yes",
        Id10021="dk",
        Id10022="Yes",
        Id10023="dk",
        instanceid="02",
    )

    # Assert that no VAs marked as duplicate and no unique_va_identifiers populated
    assert va1.unique_va_identifier == ""
    assert not va1.duplicate

    assert duplicate_of_va1.unique_va_identifier == ""
    assert not duplicate_of_va1.duplicate

    assert va2.unique_va_identifier == ""
    assert not va2.duplicate

    assert duplicate_of_va2.unique_va_identifier == ""
    assert not duplicate_of_va2.duplicate

    # Mimicking the setting where QUESTIONS_TO_AUTODETECT_DUPLICATES is defined
    settings.QUESTIONS_TO_AUTODETECT_DUPLICATES = (
        "Id10017, Id10018, Id10019, Id10020, Id10021, Id10022, Id10023"
    )

    # Run the mark_vas_as_duplicate command
    output = StringIO()
    call_command(
        "mark_vas_as_duplicate",
        stdout=output,
        stderr=output,
    )

    va1.refresh_from_db()
    duplicate_of_va1.refresh_from_db()
    va2.refresh_from_db()
    duplicate_of_va2.refresh_from_db()

    # Assert that the appropriate VAs are marked as duplicate
    assert not va1.duplicate
    assert duplicate_of_va1.duplicate

    assert not va2.duplicate
    assert duplicate_of_va2.duplicate

    assert (
        output.getvalue().strip() == "Generating unique identifiers...\n"
        "Unique identifiers generated!\n"
        "Marking existing VAs as duplicate...\n"
        "Successfully marked 2 existing VAs as duplicate!"
    )
