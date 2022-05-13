import json
from datetime import date

import pytest
from django.test import Client

from va_explorer.tests.factories import (
    CauseCodingIssueFactory,
    CauseOfDeathFactory,
    VerbalAutopsyFactory,
)
from va_explorer.users.models import User

pytestmark = pytest.mark.django_db


# Hit the trends json endpoint and make sure the counts are correct
def test_trends(user: User):
    client = Client()
    client.force_login(user=user)
    today = date.today()

    va = VerbalAutopsyFactory.create(submissiondate=today, Id10023=today)
    va2 = VerbalAutopsyFactory.create(submissiondate=today, Id10023=today)
    CauseCodingIssueFactory.create(verbalautopsy=va2, severity="error")
    CauseOfDeathFactory.create(cause="Indeterminate", verbalautopsy=va)

    response = client.get("/trends", follow=True)
    assert response.status_code == 200

    json_data = json.loads(response.content)
    va_table_data = json_data["vaTable"]

    assert va_table_data["collected"]["24"] == 2
    assert va_table_data["collected"]["1 week"] == 2
    assert va_table_data["collected"]["1 month"] == 2
    assert va_table_data["collected"]["Overall"] == 2

    assert va_table_data["coded"]["24"] == 1
    assert va_table_data["coded"]["1 week"] == 1
    assert va_table_data["coded"]["1 month"] == 1
    assert va_table_data["coded"]["Overall"] == 1

    assert va_table_data["uncoded"]["24"] == 1
    assert va_table_data["uncoded"]["1 week"] == 1
    assert va_table_data["uncoded"]["1 month"] == 1
    assert va_table_data["uncoded"]["Overall"] == 1

    assert len(json_data["issueList"]) == 1
    assert va.Id10017 in json_data["issueList"][0]["deceased"]
    assert json_data["additionalIssues"] == 0
    assert json_data["additionalIndeterminateCods"] == 0
    assert json_data["isFieldWorker"] is False


# Get the about page and make sure it returns successfully
def test_about(user: User):
    client = Client()
    client.force_login(user=user)
    response = client.get("/about/")
    assert response.status_code == 200
