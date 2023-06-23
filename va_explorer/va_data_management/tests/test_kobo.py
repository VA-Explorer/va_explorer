import os
from io import StringIO
from pathlib import Path
from unittest import mock

import pytest
from django.core.management import call_command
from requests.exceptions import HTTPError

from va_explorer.va_data_management.models import Location, VerbalAutopsy
from va_explorer.va_data_management.utils.kobo import (
    KOBO_HOST,
    download_responses,
    get_kobo_api_token,
)

pytestmark = pytest.mark.django_db

MOCK_GET_KOBO_API_TOKEN = {"token": "8sw4a4ypxthcyjpjjra7ifr3hbyxsp2ey2bf591g"}

MOCK_TEST_DOWNLOAD_JSON = (Path(__file__).parent / "kobo-data.json").read_text()


class TestGetToken:
    def test_token(self, requests_mock):
        requests_mock.get(
            f"{KOBO_HOST}/token/?format=json", json=MOCK_GET_KOBO_API_TOKEN
        )

        token = get_kobo_api_token("username", "password")
        assert token == {
            "Authorization": "Token 8sw4a4ypxthcyjpjjra7ifr3hbyxsp2ey2bf591g"
        }

    def test_error(self, requests_mock):
        requests_mock.get(f"{KOBO_HOST}/token/?format=json", status_code=403)

        with pytest.raises(HTTPError):
            error = get_kobo_api_token("invalid-username", "invalid-password")
            assert error == {"detail": "Invalid username/password."}


class TestDownloadResponse:
    def test_missing_attributes(self, requests_mock):
        err_msg = "Must specify either --token and --asset_id arguments or \
            KOBO_API_TOKEN and KOBO_ASSET_ID environment variables."
        # Missing both
        with pytest.raises(AttributeError) as e:
            download_responses(None, None)
            assert str(e.value) == err_msg
        # Missing token
        with pytest.raises(AttributeError) as e:
            download_responses(None, "TEST5yolfuacxkjibsj7nw")
            assert str(e.value) == err_msg
        # Missing asset_id
        with pytest.raises(AttributeError) as e:
            download_responses("8sw4a4ypxthcyjpjjra7ifr3hbyxsp2ey2bf591g", None)
            assert str(e.value) == err_msg

    def test_download_responses(self, requests_mock):
        requests_mock.get(
            f"{KOBO_HOST}/api/v2/assets/TEST5yolfuacxkjibsj7nw/data.json",
            text=MOCK_TEST_DOWNLOAD_JSON,
        )

        results = download_responses(
            "8sw4a4ypxthcyjpjjra7ifr3hbyxsp2ey2bf591g", "TEST5yolfuacxkjibsj7nw"
        )
        assert results.shape[0] == 2
        assert results["_uuid"][0] == "TESTf603-a193-4af3-9321-264096bf8602"


class TestImportCommand:
    err_msg = "Must specify either --token and --asset_id arguments or " \
              "KOBO_API_TOKEN and KOBO_ASSET_ID environment variables."

    @mock.patch.dict(os.environ, {}, clear=True)
    def test_missing_params(self):
        output = StringIO()
        call_command(
            "import_from_kobo",
            stdout=output,
            stderr=output,
        )
        assert output.getvalue().strip() == self.err_msg

    @mock.patch.dict(os.environ, {}, clear=True)
    def test_missing_asset_id(self):
        output = StringIO()
        call_command(
            "import_from_kobo",
            "--token=8sw4a4ypxthcyjpjjra7ifr3hbyxsp2ey2bf591g",
            stdout=output,
            stderr=output,
        )
        assert output.getvalue().strip() == self.err_msg

    @mock.patch.dict(os.environ, {}, clear=True)
    def test_missing_token(self):
        output = StringIO()
        call_command(
            "import_from_kobo",
            "--asset_id=TEST5yolfuacxkjibsj7nw",
            stdout=output,
            stderr=output,
        )
        assert output.getvalue().strip() == self.err_msg

    @mock.patch.dict(os.environ, {"KOBO_HOST": KOBO_HOST}, clear=True)
    def test_successful_run(self, requests_mock):
        requests_mock.get(
            f"{KOBO_HOST}/api/v2/assets/TEST5yolfuacxkjibsj7nw/data.json",
            text=MOCK_TEST_DOWNLOAD_JSON,
        )

        # Location gets assigned automatically/randomly.
        # If that changes in loading.py we'll need to change that here too.
        Location.add_root(name="test hospital", location_type="facility")
        assert VerbalAutopsy.objects.count() == 0

        output = StringIO()
        call_command(
            "import_from_kobo",
            "--token=8sw4a4ypxthcyjpjjra7ifr3hbyxsp2ey2bf591g",
            "--asset_id=TEST5yolfuacxkjibsj7nw",
            stdout=output,
            stderr=output,
        )
        assert (
            output.getvalue().strip()
            == "Loaded 2 verbal autopsies from Kobo (0 ignored, " \
               "0 overwritten, 0 removed as invalid)"
        )
        assert VerbalAutopsy.objects.count() == 2
        va = VerbalAutopsy.objects.get(
            instanceid="uuid:TESTf603-a193-4af3-9321-264096bf8602"
        )
        assert va.Id10010 == "james27"
        assert va.instancename == "_dec---brent_hebert_d.o.i---2017-03-07"
        assert va.Id10023 == "2016-01-21"

        # A second run on the same data should ignore those same records.
        output = StringIO()
        call_command(
            "import_from_kobo",
            "--token=8sw4a4ypxthcyjpjjra7ifr3hbyxsp2ey2bf591g",
            "--asset_id=TEST5yolfuacxkjibsj7nw",
            stdout=output,
            stderr=output,
        )
        print(10*'=' + f"{output.getvalue().strip()}" + 10*'=')
        assert (
            output.getvalue().strip()
            == "Loaded 0 verbal autopsies from Kobo (2 ignored, " \
               "0 overwritten, 0 removed as invalid)"
        )
        assert VerbalAutopsy.objects.count() == 2
