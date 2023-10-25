from io import StringIO
from pathlib import Path

import pytest
from django.core.management import call_command
from requests.exceptions import HTTPError

from va_explorer.va_data_management.models import Location, VerbalAutopsy
from va_explorer.va_data_management.utils.odk import (
    ODK_HOST,
    download_responses,
    get_odk_form,
    get_odk_login_token,
    get_odk_project_id,
)

pytestmark = pytest.mark.django_db


MOCK_GET_ODK_LOGIN_TOKEN = {
    "createdAt": "2021-03-22T19:50:42.287Z",
    "csrf": "8cc5cd13114a3cabf0d0144ff8951130",
    "expiresAt": "2030-03-23T19:50:42.287Z",
    "token": "9fee992650cf1f72273b7f3ef7d77f41",
}

MOCK_GET_ODK_PROJECT_ID = [
    {
        "archived": None,
        "createdAt": "2021-03-22T18:22:00.388Z",
        "id": 1,
        "keyId": None,
        "name": "default",
        "updatedAt": None,
    },
    {
        "archived": None,
        "createdAt": "2021-03-22T18:25:43.594Z",
        "id": 34,
        "keyId": None,
        "name": "zambia-test",
        "updatedAt": None,
    },
]

MOCK_GET_ODK_FORM = [
    {
        "createdAt": "2021-03-22T18:42:01.570Z",
        "draftToken": None,
        "enketoId": "00a04cf0f9b4456c1494e8a9429d7d7b",
        "enketoOnceId": "00a04cf0f9b4456c1494e8a9429d7d7b",
        "hash": "00a04cf0f9b4456c1494e8a9429d7d7b",
        "keyId": None,
        "name": "Dummy Form",
        "projectId": 34,
        "publishedAt": "2021-03-22T18:43:48.128Z",
        "sha": "00a04cf0f9b4456c1494e8a9429d7d7b",
        "sha256": "00a04cf0f9b4456c1494e8a9429d7d7b",
        "state": "open",
        "updatedAt": "2021-03-22T18:43:56.036Z",
        "version": "2019101701",
        "xmlFormId": "first-dummy-form",
    },
    {
        "createdAt": "2021-03-22T18:42:01.570Z",
        "draftToken": None,
        "enketoId": "2c62027c43a8fa97371e362c4bedafdb",
        "enketoOnceId": "2c62027c43a8fa97371e362c4bedafdb",
        "hash": "2c62027c43a8fa97371e362c4bedafdb",
        "keyId": None,
        "name": "Test Verbal Autopsy Form",
        "projectId": 34,
        "publishedAt": "2021-03-22T18:43:48.128Z",
        "sha": "2c62027c43a8fa97371e362c4bedafdb",
        "sha256": "2c62027c43a8fa97371e362c4bedafdb",
        "state": "open",
        "updatedAt": "2021-03-22T18:43:56.036Z",
        "version": "2019101701",
        "xmlFormId": "va_who_v1_5_2",
    },
]

MOCK_TEST_DOWNLOAD_CSV = (Path(__file__).parent / "odk-data.csv").read_text()
MOCK_TEST_DOWNLOAD_JSON = (Path(__file__).parent / "odk-data.json").read_text()


class TestLogin:
    def test_token(self, requests_mock):
        requests_mock.post(f"{ODK_HOST}/v1/sessions", json=MOCK_GET_ODK_LOGIN_TOKEN)

        token = get_odk_login_token("email", "password")

        assert token == {"Authorization": "Bearer 9fee992650cf1f72273b7f3ef7d77f41"}

    def test_response_error(self, requests_mock):
        requests_mock.post(f"{ODK_HOST}/v1/sessions", status_code=400)

        with pytest.raises(HTTPError):
            get_odk_login_token("bad-email", "bad-password")


class TestGetProjectID:
    def test_with_project_name(self, requests_mock):
        requests_mock.get(f"{ODK_HOST}/v1/projects/", json=MOCK_GET_ODK_PROJECT_ID)

        token = {"Authorization": "Bearer test"}
        project_id = get_odk_project_id(token, "zambia-test")

        assert project_id == 34

    def test_missing_project_name(self, requests_mock):
        requests_mock.get(f"{ODK_HOST}/v1/projects/", json=MOCK_GET_ODK_PROJECT_ID)
        token = {"Authorization": "Bearer test"}

        with pytest.raises(
            ValueError,
            match="No projects with name 'nothing-here' were returned from ODK",
        ):
            get_odk_project_id(token, "nothing-here")


class TestGetForm:
    def test_blank_response(self, requests_mock):
        requests_mock.get(f"{ODK_HOST}/v1/projects/1234/forms", json=[])
        token = {"Authorization": "Bearer test"}

        with pytest.raises(
            ValueError,
            match="No forms for project with ID '1234' were returned from ODK.",
        ):
            get_odk_form(token, 1234, form_id="va_who_v1_5_2")

    def test_missing_name_and_id(self, requests_mock):
        requests_mock.get(f"{ODK_HOST}/v1/projects/34/forms", json=MOCK_GET_ODK_FORM)
        token = {"Authorization": "Bearer test"}

        with pytest.raises(
            AttributeError, match="Must specify either form_name or form_id argument."
        ):
            get_odk_form(token, 34)

    def test_get_by_id(self, requests_mock):
        requests_mock.get(f"{ODK_HOST}/v1/projects/34/forms", json=MOCK_GET_ODK_FORM)

        token = {"Authorization": "Bearer test"}
        form = get_odk_form(token, 34, form_id="va_who_v1_5_2")

        assert form["xmlFormId"] == "va_who_v1_5_2"

    def test_get_by_name(self, requests_mock):
        requests_mock.get(f"{ODK_HOST}/v1/projects/34/forms", json=MOCK_GET_ODK_FORM)

        token = {"Authorization": "Bearer test"}
        form = get_odk_form(token, 34, form_name="Test Verbal Autopsy Form")

        assert form["xmlFormId"] == "va_who_v1_5_2"

    def test_id_has_precedence(self, requests_mock):
        requests_mock.get(f"{ODK_HOST}/v1/projects/34/forms", json=MOCK_GET_ODK_FORM)

        token = {"Authorization": "Bearer test"}
        form = get_odk_form(
            token,
            34,
            form_id="va_who_v1_5_2",
            form_name="bad name but it does not matter",
        )

        assert form["xmlFormId"] == "va_who_v1_5_2"

    def test_bad_name_and_id(self, requests_mock):
        requests_mock.get(f"{ODK_HOST}/v1/projects/34/forms", json=MOCK_GET_ODK_FORM)

        token = {"Authorization": "Bearer test"}
        with pytest.raises(
            ValueError,
            match="No forms found with name 'bad name' or ID 'bad-id' were found in ODK.",
        ):
            get_odk_form(token, 34, form_id="bad-id", form_name="bad name")


class TestDownloadResponse:
    def test_invalid_attributes(self, requests_mock):
        requests_mock.post(f"{ODK_HOST}/v1/sessions", json=MOCK_GET_ODK_LOGIN_TOKEN)
        requests_mock.get(f"{ODK_HOST}/v1/projects/", json=MOCK_GET_ODK_PROJECT_ID)

        # No project or form causes an error.
        with pytest.raises(
            AttributeError,
            match="Must specify either project_name or project_id argument.",
        ):
            download_responses("email", "password")

        # No form_id or form_name causes an error.
        with pytest.raises(
            AttributeError, match="Must specify either form_name or form_id argument."
        ):
            download_responses("email", "password", project_id="123")

        # No project_id or project_name causes an error.
        with pytest.raises(
            AttributeError,
            match="Must specify either project_name or project_id argument.",
        ):
            download_responses("email", "password", form_id="123")

        # Good project and form, but bad format causes an error.
        with pytest.raises(
            AttributeError, match="The fmt argument must either be json or csv."
        ):
            download_responses(
                "email", "password", project_id="1234", form_id="123", fmt="xlsx"
            )

    @pytest.mark.parametrize(
        "kwargs",
        [
            # project_name, form_name
            {
                "project_name": "zambia-test",
                "form_name": "Test Verbal Autopsy Form",
                "fmt": "json",
            },
            {
                "project_name": "zambia-test",
                "form_name": "Test Verbal Autopsy Form",
                "fmt": "csv",
            },
            # project_name, form_id
            {"project_name": "zambia-test", "form_id": "va_who_v1_5_2", "fmt": "json"},
            {"project_name": "zambia-test", "form_id": "va_who_v1_5_2", "fmt": "csv"},
            # project_id, form_name
            {
                "project_id": "34",
                "form_name": "Test Verbal Autopsy Form",
                "fmt": "json",
            },
            {"project_id": "34", "form_name": "Test Verbal Autopsy Form", "fmt": "csv"},
            # project_id, form_id
            {"project_id": "34", "form_id": "va_who_v1_5_2", "fmt": "json"},
            {"project_id": "34", "form_id": "va_who_v1_5_2", "fmt": "csv"},
        ],
    )
    def test_download_response(self, requests_mock, kwargs):
        requests_mock.post(f"{ODK_HOST}/v1/sessions", json=MOCK_GET_ODK_LOGIN_TOKEN)
        requests_mock.get(f"{ODK_HOST}/v1/projects/", json=MOCK_GET_ODK_PROJECT_ID)
        requests_mock.get(f"{ODK_HOST}/v1/projects/34/forms", json=MOCK_GET_ODK_FORM)
        requests_mock.get(
            f"{ODK_HOST}/v1/projects/34/forms/va_who_v1_5_2/submissions.csv",
            text=MOCK_TEST_DOWNLOAD_CSV,
        )
        requests_mock.get(
            f"{ODK_HOST}/v1/projects/34/forms/va_who_v1_5_2.svc/Submissions",
            text=MOCK_TEST_DOWNLOAD_JSON,
        )

        result = download_responses("email", "password", **kwargs)
        assert len(result) == 1
        assert result["Id10007"][0] == "test data"


class TestImportCommand:
    def test_missing_email_password(self):
        output = StringIO()
        call_command(
            "import_from_odk",
            stdout=output,
            stderr=output,
        )
        assert (
            output.getvalue().strip()
            == "Must specify either --email and --password arguments or "
            "ODK_EMAIL and ODK_PASSWORD environment variables."
        )

    def test_missing_project(self):
        output = StringIO()
        call_command(
            "import_from_odk",
            "--email=test",
            "--password=test",
            stdout=output,
            stderr=output,
        )
        assert (
            output.getvalue().strip()
            == "Must specify either --project-id or --project-name arguments; not both"
        )

    def test_both_project_id_and_project_name(self):
        output = StringIO()
        call_command(
            "import_from_odk",
            "--email=test",
            "--password=test",
            "--project-id=1234",
            "--project-name=test",
            stdout=output,
            stderr=output,
        )
        assert (
            output.getvalue().strip()
            == "Must specify either --project-id or --project-name arguments; not both"
        )

    def test_missing_form(self):
        output = StringIO()
        call_command(
            "import_from_odk",
            "--email=test",
            "--password=test",
            "--project-id=1234",
            stdout=output,
            stderr=output,
        )
        assert (
            output.getvalue().strip()
            == "Must specify either --form-id or --form-name arguments; not both"
        )

    def test_both_form_id_and_form_name(self):
        output = StringIO()
        call_command(
            "import_from_odk",
            "--email=test",
            "--password=test",
            "--project-id=1234",
            "--form-id=1234",
            "--form-name=test",
            stdout=output,
            stderr=output,
        )
        assert (
            output.getvalue().strip()
            == "Must specify either --form-id or --form-name arguments; not both"
        )

    @pytest.mark.parametrize(
        "command_args",
        [
            ["--project-name=zambia-test", "--form-id=va_who_v1_5_2"],
            ["--project-name=zambia-test", "--form-name=Test Verbal Autopsy Form"],
            ["--project-id=34", "--form-id=va_who_v1_5_2"],
            ["--project-id=34", "--form-name=Test Verbal Autopsy Form"],
        ],
    )
    def test_successful_runs(self, requests_mock, command_args):
        requests_mock.post(f"{ODK_HOST}/v1/sessions", json=MOCK_GET_ODK_LOGIN_TOKEN)
        requests_mock.get(f"{ODK_HOST}/v1/projects/", json=MOCK_GET_ODK_PROJECT_ID)
        requests_mock.get(f"{ODK_HOST}/v1/projects/34/forms", json=MOCK_GET_ODK_FORM)
        requests_mock.get(
            f"{ODK_HOST}/v1/projects/34/forms/va_who_v1_5_2/submissions.csv",
            text=MOCK_TEST_DOWNLOAD_CSV,
        )
        requests_mock.get(
            f"{ODK_HOST}/v1/projects/34/forms/va_who_v1_5_2.svc/Submissions",
            text=MOCK_TEST_DOWNLOAD_JSON,
        )

        # Location gets assigned automatically/randomly.
        # If that changes in loading.py we'll need to change that here too.
        Location.add_root(name="test location", location_type="facility")

        assert VerbalAutopsy.objects.count() == 0

        output = StringIO()
        call_command(
            "import_from_odk",
            "--email=test",
            "--password=test",
            *command_args,
            stdout=output,
            stderr=output,
        )

        assert (
            output.getvalue().strip()
            == "Loaded 1 verbal autopsies from ODK (0 ignored, 0 removed as outdated)"
        )
        assert VerbalAutopsy.objects.count() == 1
        assert (
            VerbalAutopsy.objects.get(instanceid="test-instance").Id10007 == "test data"
        )

        # Run it again and it should ignore the same record.

        output = StringIO()
        call_command(
            "import_from_odk",
            "--email=test",
            "--password=test",
            *command_args,
            stdout=output,
            stderr=output,
        )

        assert (
            output.getvalue().strip()
            == "Loaded 0 verbal autopsies from ODK (1 ignored, 0 removed as outdated)"
        )
        assert VerbalAutopsy.objects.count() == 1
