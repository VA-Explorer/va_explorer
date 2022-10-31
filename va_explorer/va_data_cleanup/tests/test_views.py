import pytest
from django.contrib.auth.models import Permission
from django.test import Client

from va_explorer.tests.factories import GroupFactory, UserFactory, VerbalAutopsyFactory
from va_explorer.users.models import User

pytestmark = pytest.mark.django_db


@pytest.fixture
def questions_to_autodetect_duplicates():
    return "Id10017, Id10010"


@pytest.fixture
def view_datacleanup_group():
    can_view_datacleanup = Permission.objects.filter(
        codename="view_datacleanup"
    ).first()
    return GroupFactory.create(permissions=[can_view_datacleanup])


@pytest.fixture
def download_group():
    can_download = Permission.objects.filter(codename="download").first()
    return GroupFactory.create(permissions=[can_download])


@pytest.fixture
def bulk_download_group():
    can_bulk_download = Permission.objects.filter(codename="bulk_download").first()
    return GroupFactory.create(permissions=[can_bulk_download])


# View the index page
def test_index_with_valid_permission(
    user: User, settings, view_datacleanup_group, questions_to_autodetect_duplicates
):
    settings.QUESTIONS_TO_AUTODETECT_DUPLICATES = questions_to_autodetect_duplicates
    user = UserFactory.create(groups=[view_datacleanup_group])

    client = Client()
    client.force_login(user=user)

    VerbalAutopsyFactory.create(Id10017="Victim name", Id10010="Interviewer name")
    VerbalAutopsyFactory.create(Id10017="Victim name", Id10010="Interviewer name")

    response = client.get("/va_data_cleanup/")

    assert response.status_code == 200


# A user must have the view_datacleanup permission to view the index
def test_index_with_invalid_permission(
    user: User, settings, questions_to_autodetect_duplicates
):
    settings.QUESTIONS_TO_AUTODETECT_DUPLICATES = questions_to_autodetect_duplicates
    user = UserFactory.create()

    client = Client()
    client.force_login(user=user)

    response = client.get("/va_data_cleanup/")
    assert response.status_code == 403


def test_index_with_valid_permission_and_invalid_configuration(
    user: User, settings, view_datacleanup_group
):
    settings.QUESTIONS_TO_AUTODETECT_DUPLICATES = None

    user = UserFactory.create(groups=[view_datacleanup_group])

    client = Client()
    client.force_login(user=user)

    response = client.get("/va_data_cleanup/")
    assert response.status_code == 200
    assert (
        bytes(
            "Your system is currently not configured to automatically flag Verbal Autopsies as potential duplicates.",
            "utf-8",
        )
        in response.content
    )


def test_download_with_valid_permission(
    user: User,
    settings,
    view_datacleanup_group,
    download_group,
    questions_to_autodetect_duplicates,
):
    settings.QUESTIONS_TO_AUTODETECT_DUPLICATES = questions_to_autodetect_duplicates
    user = UserFactory.create(groups=[view_datacleanup_group, download_group])

    client = Client()
    client.force_login(user=user)

    VerbalAutopsyFactory.create(Id10017="Victim name", Id10010="Interviewer name")
    va = VerbalAutopsyFactory.create(Id10017="Victim name", Id10010="Interviewer name")

    response = client.get(f"/va_data_cleanup/download/{va.id}")

    assert response.status_code == 200
    assert response.headers["content-type"] == "text/csv"


def test_download_with_invalid_permission(
    user: User, settings, view_datacleanup_group, questions_to_autodetect_duplicates
):
    settings.QUESTIONS_TO_AUTODETECT_DUPLICATES = questions_to_autodetect_duplicates
    user = UserFactory.create(groups=[view_datacleanup_group])

    client = Client()
    client.force_login(user=user)

    VerbalAutopsyFactory.create(Id10017="Victim name", Id10010="Interviewer name")
    va = VerbalAutopsyFactory.create(Id10017="Victim name", Id10010="Interviewer name")

    response = client.get(f"/va_data_cleanup/download/{va.id}")

    assert response.status_code == 403
    assert response.headers["content-type"] == "text/html; charset=utf-8"


# Test if a user arbitrarily passes in a non-duplicate VA, 403 raised
def test_download_with_valid_permission_non_duplicate_va(
    user: User, settings, view_datacleanup_group, questions_to_autodetect_duplicates
):
    settings.QUESTIONS_TO_AUTODETECT_DUPLICATES = questions_to_autodetect_duplicates
    user = UserFactory.create(groups=[view_datacleanup_group])

    client = Client()
    client.force_login(user=user)

    va = VerbalAutopsyFactory.create(Id10017="Victim name", Id10010="Interviewer name")
    VerbalAutopsyFactory.create(Id10017="Victim name", Id10010="Interviewer name")

    response = client.get(f"/va_data_cleanup/download/{va.id}")

    assert response.status_code == 403
    assert response.headers["content-type"] == "text/html; charset=utf-8"


def test_bulk_download_with_valid_permission(
    user: User,
    settings,
    view_datacleanup_group,
    bulk_download_group,
    questions_to_autodetect_duplicates,
):
    settings.QUESTIONS_TO_AUTODETECT_DUPLICATES = questions_to_autodetect_duplicates
    user = UserFactory.create(groups=[view_datacleanup_group, bulk_download_group])

    client = Client()
    client.force_login(user=user)

    VerbalAutopsyFactory.create(Id10017="Victim name", Id10010="Interviewer name")
    VerbalAutopsyFactory.create(Id10017="Victim name", Id10010="Interviewer name")

    response = client.get("/va_data_cleanup/download_all")

    assert response.status_code == 200
    assert response.headers["content-type"] == "text/csv"


def test_bulk_download_with_invalid_permission(
    user: User, settings, view_datacleanup_group, questions_to_autodetect_duplicates
):
    settings.QUESTIONS_TO_AUTODETECT_DUPLICATES = questions_to_autodetect_duplicates
    user = UserFactory.create(groups=[view_datacleanup_group])

    client = Client()
    client.force_login(user=user)

    VerbalAutopsyFactory.create(Id10017="Victim name", Id10010="Interviewer name")
    VerbalAutopsyFactory.create(Id10017="Victim name", Id10010="Interviewer name")

    response = client.get("/va_data_cleanup/download_all")

    assert response.status_code == 403
    assert response.headers["content-type"] == "text/html; charset=utf-8"
