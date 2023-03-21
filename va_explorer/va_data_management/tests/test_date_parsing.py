import pytest
from numpy import nan

from va_explorer.va_data_management.models import VerbalAutopsy
from va_explorer.va_data_management.utils.date_parsing import get_interview_date

pytestmark = pytest.mark.django_db


# ensure that when interview date field not available, Id10011 is used to
# determine date of interview
def test_interview_date_logic():
    date1 = "2021-04-19T13:53:07.928Z"
    date2 = "2020-05-19T20:18:12.124+02:00"
    empty_string = "dk"

    va1 = VerbalAutopsy(Id10012=date1)
    va2 = VerbalAutopsy(Id10012=nan, Id10011=date2)
    va3 = VerbalAutopsy(Id10012="", Id10011="")

    date_res_1 = get_interview_date(va1, parse=True, empty_string=empty_string)
    date_res_2 = get_interview_date(va2, parse=True, empty_string=empty_string)
    date_res_3 = get_interview_date(va3, parse=True, empty_string=empty_string)

    assert date_res_1 == "2021-04-19"
    assert date_res_2 == "2020-05-19"
    assert date_res_3 == empty_string
