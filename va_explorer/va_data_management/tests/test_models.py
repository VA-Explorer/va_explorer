import pytest

from va_explorer.tests.factories import (
    CauseCodingIssueFactory,
    CauseOfDeathFactory,
    DhisStatusFactory,
    VerbalAutopsyFactory,
)
from va_explorer.va_data_management.models import (
    CauseCodingIssue,
    CauseOfDeath,
    DhisStatus,
    VerbalAutopsy,
)

pytestmark = pytest.mark.django_db


@pytest.fixture
def questions_to_autodetect_duplicates():
    return "Id10017, Id10018, Id10019, Id10020, Id10021, Id10022, Id10023"


def test_save_mark_duplicates_with_autodetect_duplicates(
    settings, questions_to_autodetect_duplicates
):
    settings.QUESTIONS_TO_AUTODETECT_DUPLICATES = questions_to_autodetect_duplicates

    va1 = VerbalAutopsyFactory.create(
        Id10017="Bob",
        Id10018="Jones",
        Id10019="Male",
        Id10020="Yes",
        Id10021="1/1/60",
        Id10022="Yes",
        Id10023="1/5/21",
        instanceid="00",
    )
    va2 = VerbalAutopsyFactory.create(
        Id10017="Bob",
        Id10018="Jones",
        Id10019="Male",
        Id10020="Yes",
        Id10021="1/1/60",
        Id10022="Yes",
        Id10023="1/5/21",
        instanceid="01",
    )
    va3 = VerbalAutopsyFactory.create(
        Id10017="Bob",
        Id10018="Jones",
        Id10019="Male",
        Id10020="Yes",
        Id10021="1/1/60",
        Id10022="Yes",
        Id10023="1/5/21",
        instanceid="02",
    )
    va4 = VerbalAutopsyFactory.create(
        Id10017="Barb",
        Id10018="Jones",
        Id10019="Female",
        Id10020="Yes",
        Id10021="1/1/60",
        Id10022="Yes",
        Id10023="1/5/21",
        instanceid="03",
    )
    va5 = VerbalAutopsyFactory.create(
        Id10017="Barb",
        Id10018="Jones",
        Id10019="Female",
        Id10020="Yes",
        Id10021="1/1/60",
        Id10022="Yes",
        Id10023="1/5/21",
        instanceid="04",
    )
    va6 = VerbalAutopsyFactory.create(
        Id10017="Tom",
        Id10018="Jones",
        Id10019="Male",
        Id10020="No",
        Id10021="",
        Id10022="No",
        Id10023="",
        instanceid="05",
    )

    va1.refresh_from_db()
    va2.refresh_from_db()
    va3.refresh_from_db()
    va4.refresh_from_db()
    va5.refresh_from_db()
    va6.refresh_from_db()

    assert not va1.duplicate
    assert va2.duplicate
    assert va3.duplicate
    assert not va4.duplicate
    assert va5.duplicate
    assert not va6.duplicate


def test_save_updates_unique_va_identifier_with_autodetect_duplicates(
    settings, questions_to_autodetect_duplicates
):
    settings.QUESTIONS_TO_AUTODETECT_DUPLICATES = questions_to_autodetect_duplicates

    va1 = VerbalAutopsyFactory.create(
        Id10017="Bob",
        Id10018="Jones",
        Id10019="Male",
        Id10020="Yes",
        Id10021="1/1/60",
        Id10022="Yes",
        Id10023="1/5/21",
        instanceid="00",
    )

    assert va1.unique_va_identifier == "840ba941ac6e608962f86eb05659bad1"

    va1.Id10017 = "Robert"
    va1.save()
    assert va1.unique_va_identifier == "690b7d0bd136e0e4f7e732b86cbeb12e"

    va1.Id10018 = "Jonesy"
    va1.save()
    assert va1.unique_va_identifier == "811f7f36f5da61dae92f12caa46ffad9"

    va1.Id10019 = "dk"
    va1.save()
    assert va1.unique_va_identifier == "47c75220e6a1e7594e98bba4f0d0c003"

    va1.Id10020 = "dk"
    va1.save()
    assert va1.unique_va_identifier == "a567709589e739616a6b77441d871767"

    va1.Id10021 = "1/1/61"
    va1.save()
    assert va1.unique_va_identifier == "81616374fab861f1630b288a30cd0447"

    va1.Id10022 = "No"
    va1.save()
    assert va1.unique_va_identifier == "52b23a15634033697d1fa7d3988f3f27"

    va1.Id10023 = ""
    va1.save()
    assert va1.unique_va_identifier == "3df591b678ea5e730966fc63ac77b687"

    va1.Id10002 = "yes"
    va1.save()
    assert va1.unique_va_identifier == "3df591b678ea5e730966fc63ac77b687"


def test_save_does_not_populate_unique_va_identifier_without_autodetect_duplicates(
    settings,
):
    settings.QUESTIONS_TO_AUTODETECT_DUPLICATES = None

    va1 = VerbalAutopsyFactory.create(
        Id10017="Bob",
        Id10018="Jones",
        Id10019="Male",
        Id10020="Yes",
        Id10021="1/1/60",
        Id10022="Yes",
        Id10023="1/5/21",
        instanceid="00",
    )

    assert va1.unique_va_identifier == ""


def test_save_updates_duplicates_with_autodetect_duplicates(
    settings, questions_to_autodetect_duplicates
):
    settings.QUESTIONS_TO_AUTODETECT_DUPLICATES = questions_to_autodetect_duplicates

    va1 = VerbalAutopsyFactory.create(
        Id10017="Bob",
        Id10018="Jones",
        Id10019="Male",
        Id10020="Yes",
        Id10021="1/1/60",
        Id10022="Yes",
        Id10023="1/5/21",
        instanceid="00",
    )
    va2 = VerbalAutopsyFactory.create(
        Id10017="Bob",
        Id10018="Jones",
        Id10019="Male",
        Id10020="Yes",
        Id10021="1/1/60",
        Id10022="Yes",
        Id10023="1/5/21",
        instanceid="00",
    )
    va3 = VerbalAutopsyFactory.create(
        Id10017="Bob",
        Id10018="Jones",
        Id10019="Male",
        Id10020="Yes",
        Id10021="1/1/60",
        Id10022="Yes",
        Id10023="1/5/21",
        instanceid="00",
    )
    va4 = VerbalAutopsyFactory.create(
        Id10017="Bob",
        Id10018="Jones",
        Id10019="Male",
        Id10020="Yes",
        Id10021="1/1/60",
        Id10022="No",
        Id10023="1/5/21",
        instanceid="00",
    )

    va1.refresh_from_db()
    va2.refresh_from_db()
    va3.refresh_from_db()
    va4.refresh_from_db()

    assert not va1.duplicate
    assert va2.duplicate
    assert va3.duplicate
    assert not va4.duplicate

    va1.Id10022 = "No"
    va1.save()

    va1.refresh_from_db()
    va2.refresh_from_db()
    va3.refresh_from_db()
    va4.refresh_from_db()

    assert not va1.duplicate
    assert not va2.duplicate
    assert va3.duplicate
    assert va4.duplicate


def test_save_does_not_update_duplicates_without_autodetect_duplicates(settings):
    settings.QUESTIONS_TO_AUTODETECT_DUPLICATES = None

    va1 = VerbalAutopsyFactory.create(
        Id10017="Bob",
        Id10018="Jones",
        Id10019="Male",
        Id10020="Yes",
        Id10021="1/1/60",
        Id10022="Yes",
        Id10023="1/5/21",
        instanceid="00",
    )
    va2 = VerbalAutopsyFactory.create(
        Id10017="Bob",
        Id10018="Jones",
        Id10019="Male",
        Id10020="Yes",
        Id10021="1/1/60",
        Id10022="Yes",
        Id10023="1/5/21",
        instanceid="00",
    )

    va1.refresh_from_db()
    va2.refresh_from_db()

    assert not va1.duplicate
    assert not va2.duplicate


def test_soft_deletion_of_verbal_autopsy():
    va = VerbalAutopsyFactory.create()
    assert VerbalAutopsy.objects.all().count() == 1

    # VA delete() is a soft delete in which the deleted_at timestamp is set
    va.delete()
    va.refresh_from_db()

    # Returns only objects where deleted_at = None
    assert VerbalAutopsy.objects.all().count() == 0
    # Returns all objects
    assert VerbalAutopsy.all_objects.count() == 1
    assert va.deleted_at is not None

    # VA hard_delete() removes the VA from the database
    va.hard_delete()

    assert VerbalAutopsy.objects.all().count() == 0
    assert VerbalAutopsy.all_objects.count() == 0


def test_related_model_managers():
    va = VerbalAutopsyFactory.create()
    CauseOfDeathFactory.create(verbalautopsy=va)
    CauseCodingIssueFactory.create(verbalautopsy=va)
    DhisStatusFactory.create(verbalautopsy=va)

    assert VerbalAutopsy.objects.all().count() == 1
    assert CauseOfDeath.objects.all().count() == 1
    assert CauseCodingIssue.objects.all().count() == 1
    assert DhisStatus.objects.all().count() == 1

    va.delete()

    assert VerbalAutopsy.objects.all().count() == 0
    assert CauseOfDeath.objects.all().count() == 0
    assert CauseCodingIssue.objects.all().count() == 0
    assert DhisStatus.objects.all().count() == 0
