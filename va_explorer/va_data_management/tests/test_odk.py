import json
from io import StringIO
from pathlib import Path

import pytest
from django.core.management import call_command

from va_explorer.va_data_management.models import Location
from va_explorer.va_data_management.models import VerbalAutopsy
from va_explorer.va_data_management.utils.odk import get_odk_login_token
from va_explorer.va_data_management.utils.odk import get_odk_form
from va_explorer.va_data_management.utils.odk import get_odk_project_id
from va_explorer.va_data_management.utils.odk import download_responses

pytestmark = pytest.mark.django_db


MOCK_GET_ODK_LOGIN_TOKEN = {
    "createdAt": "2021-03-22T19:50:42.287Z",
    "csrf": "8cc5cd13114a3cabf0d0144ff8951130",
    "expiresAt": "2030-03-23T19:50:42.287Z",
    "token": "9fee992650cf1f72273b7f3ef7d77f41"
}

MOCK_GET_ODK_PROJECT_ID = [
    {
        "archived": None,
        "createdAt": "2021-03-22T18:22:00.388Z",
        "id": 1,
        "keyId": None,
        "name": "default",
        "updatedAt": None
    },
    {
        "archived": None,
        "createdAt": "2021-03-22T18:25:43.594Z",
        "id": 34,
        "keyId": None,
        "name": "zambia-test",
        "updatedAt": None
    }
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
        "xmlFormId": "first-dummy-form"
    },
    {
        "createdAt": "2021-03-22T18:42:01.570Z",
        "draftToken": None,
        "enketoId": "2c62027c43a8fa97371e362c4bedafdb",
        "enketoOnceId": "2c62027c43a8fa97371e362c4bedafdb",
        "hash": "2c62027c43a8fa97371e362c4bedafdb",
        "keyId": None,
        "name": "2016 WHO Verbal Autopsy Form 1.5.2",
        "projectId": 34,
        "publishedAt": "2021-03-22T18:43:48.128Z",
        "sha": "2c62027c43a8fa97371e362c4bedafdb",
        "sha256": "2c62027c43a8fa97371e362c4bedafdb",
        "state": "open",
        "updatedAt": "2021-03-22T18:43:56.036Z",
        "version": "2019101701",
        "xmlFormId": "va_who_v1_5_2"
    }
]

MOCK_TEST_DOWNLOAD_CSV = (Path(__file__).parent / 'odk-data.csv').read_text()
MOCK_TEST_DOWNLOAD_JSON = (Path(__file__).parent / 'odk-data.json').read_text()


def test_get_odk_login_token(requests_mock):
    requests_mock.post('http://127.0.0.1:5002/v1/sessions', json=MOCK_GET_ODK_LOGIN_TOKEN)

    token = get_odk_login_token('email', 'password')

    assert token == {'Authorization': 'Bearer 9fee992650cf1f72273b7f3ef7d77f41'}


def test_get_odk_project_id(requests_mock):
    requests_mock.get('http://127.0.0.1:5002/v1/projects/', json=MOCK_GET_ODK_PROJECT_ID)

    token = {'Authorization': 'Bearer test'}
    project_id = get_odk_project_id(token, 'zambia-test')

    assert project_id == 34


def get_odk_project_id_missing(requests_mock):
    requests_mock.get('http://127.0.0.1:5002/v1/projects/', json=MOCK_GET_ODK_PROJECT_ID)

    with pytest.raises(ValueError):
        token = {'Authorization': 'Bearer test'}        
        get_odk_project_id(token, 'nothing-here')


def test_get_odk_form(requests_mock):
    requests_mock.get('http://127.0.0.1:5002/v1/projects/34/forms', json=MOCK_GET_ODK_FORM)

    token = {'Authorization': 'Bearer test'}
    form = get_odk_form(token, 34)

    assert form['xmlFormId'] == 'va_who_v1_5_2'


def test_get_odk_form_missing(requests_mock):
    requests_mock.get('http://127.0.0.1:5002/v1/projects/1234/forms', json=[])

    with pytest.raises(ValueError):
        token = {'Authorization': 'Bearer test'}
        form = get_odk_form(token, 1234)


@pytest.mark.parametrize("kwargs", [
    {'project_name': 'zambia-test', 'fmt': 'json'},
    {'project_name': 'zambia-test', 'fmt': 'csv'},
    {'project_id': '34', 'fmt': 'json'},
    {'project_id': '34', 'fmt': 'csv'},
])
def test_download_response(requests_mock, kwargs):
    requests_mock.post('http://127.0.0.1:5002/v1/sessions', json=MOCK_GET_ODK_LOGIN_TOKEN)
    requests_mock.get('http://127.0.0.1:5002/v1/projects/', json=MOCK_GET_ODK_PROJECT_ID)
    requests_mock.get('http://127.0.0.1:5002/v1/projects/34/forms', json=MOCK_GET_ODK_FORM)
    requests_mock.get('http://127.0.0.1:5002/v1/projects/34/forms/va_who_v1_5_2/submissions.csv', text=MOCK_TEST_DOWNLOAD_CSV)
    requests_mock.get('http://127.0.0.1:5002/v1/projects/34/forms/va_who_v1_5_2.svc/Submissions', text=MOCK_TEST_DOWNLOAD_JSON)

    result = download_responses('email', 'password', **kwargs)
    assert len(result) == 1
    assert result['Id10007'][0] == 'test data'


def test_download_response_error(requests_mock):
    requests_mock.post('http://127.0.0.1:5002/v1/sessions', json=MOCK_GET_ODK_LOGIN_TOKEN)
    requests_mock.get('http://127.0.0.1:5002/v1/projects/', json=MOCK_GET_ODK_PROJECT_ID)
  
    # No project_id or project_name causes an error.
    with pytest.raises(AttributeError):
        download_responses('email', 'password')

    # Bad format causes an error.
    with pytest.raises(AttributeError):
        download_responses('email', 'password', project_id='1234', fmt='xlsx')


@pytest.mark.parametrize("project_arg", [
    '--project-name=zambia-test',
    '--project-id=34',
])
def test_import_from_odk_command(requests_mock, project_arg):
    requests_mock.post('http://127.0.0.1:5002/v1/sessions', json=MOCK_GET_ODK_LOGIN_TOKEN)
    requests_mock.get('http://127.0.0.1:5002/v1/projects/', json=MOCK_GET_ODK_PROJECT_ID)
    requests_mock.get('http://127.0.0.1:5002/v1/projects/34/forms', json=MOCK_GET_ODK_FORM)
    requests_mock.get('http://127.0.0.1:5002/v1/projects/34/forms/va_who_v1_5_2/submissions.csv', text=MOCK_TEST_DOWNLOAD_CSV)
    requests_mock.get('http://127.0.0.1:5002/v1/projects/34/forms/va_who_v1_5_2.svc/Submissions', text=MOCK_TEST_DOWNLOAD_JSON)

    # Location gets assigned automatically/randomly.
    # If that changes in loading.py we'll need to change that here too.
    Location.objects.create(name='test location', location_type='facility', depth=0, numchild=0, path='0001')

    assert VerbalAutopsy.objects.count() == 0

    output = StringIO()

    call_command(
        "import_from_odk", 
        "--email=test",
        "--password=test",
        project_arg,
        stdout=output,
        stderr=output,
    )

    assert output.getvalue().startswith("Loaded 1 verbal autopsies from ODK")
    assert VerbalAutopsy.objects.get(instanceid='test-instance').Id10007 == 'test data'
