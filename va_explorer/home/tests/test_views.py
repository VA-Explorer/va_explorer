import pytest
from django.test import Client
from va_explorer.users.models import User
from va_explorer.tests.factories import VerbalAutopsyFactory, LocationFactory
from dateutil.relativedelta import relativedelta


pytestmark = pytest.mark.django_db

# Get the index and make sure
def test_index(user: User):
    client = Client()
    client.force_login(user=user)
    today = date.today()
    va = VerbalAutopsyFactory.create(submissiondate=today, Id10023=today)
    response = client.get("/")
    assert response.status_code == 200
    assert response.context['vas_collected_24_hours'] == 1
    assert response.context['vas_collected_1_week'] == 1
    assert response.context['vas_collected_1_month'] == 1
    assert response.context['vas_collected_overall'] == 1
    assert response.context['vas_coded_24_hours'] == 0
    assert response.context['vas_coded_1_week'] == 0
    assert response.context['vas_coded_1_month'] == 0
    assert response.context['vas_coded_overall'] == 0
    assert response.context['vas_uncoded_24_hours'] == 1
    assert response.context['vas_uncoded_1_week'] == 1
    assert response.context['vas_uncoded_1_month'] == 1
    assert response.context['vas_uncoded_overall'] == 1
    assert len(response.context['issue_list']) == 1
    assert va.Id10017 in response.context['issue_list'][0]['deceased']
    assert response.context['additional_issues'] == 0


# Get the about page and make sure it returns successfully
def test_about(user: User):
    client = Client()
    client.force_login(user=user)
    va = VerbalAutopsyFactory.create()
    response = client.get(f"/about/")
    assert response.status_code == 200
