import json
from datetime import date

import pytest
from django.test import Client

from va_explorer.tests.factories import VerbalAutopsyFactory
from va_explorer.users.models import User

pytestmark = pytest.mark.django_db


# Get trends json endpoint and make sure the counts are correct
def test_trends(user: User):
    client = Client()
    client.force_login(user=user)
    today = date.today()
    va = VerbalAutopsyFactory.create(submissiondate=today, Id10023=today)

    response = client.get("/trends", follow=True)
    assert response.status_code == 200

    json_data = json.loads(response.content)
    va_table_data = json_data["vaTable"]

    assert va_table_data["collected"]["24"] == 1
    assert va_table_data["collected"]["1 week"] == 1
    assert va_table_data["collected"]["1 month"] == 1
    assert va_table_data["collected"]["Overall"] == 1

    assert va_table_data["coded"]["24"] == 0
    assert va_table_data["coded"]["1 week"] == 0
    assert va_table_data["coded"]["1 month"] == 0
    assert va_table_data["coded"]["Overall"] == 0

    assert va_table_data["uncoded"]["24"] == 1
    assert va_table_data["uncoded"]["1 week"] == 1
    assert va_table_data["uncoded"]["1 month"] == 1
    assert va_table_data["uncoded"]["Overall"] == 1

    assert len(json_data["issueList"]) == 1
    assert va.Id10017 in json_data["issueList"][0]["deceased"]
    assert json_data["additionalIssues"] == 0


# Get the about page and make sure it returns successfully
def test_about(user: User):
    client = Client()
    client.force_login(user=user)
    response = client.get("/about/")
    assert response.status_code == 200
