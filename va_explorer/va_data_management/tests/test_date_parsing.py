import pytest
from numpy import nan

from va_explorer.va_data_management.models import VerbalAutopsy
from va_explorer.va_data_management.utils.date_parsing import get_submissiondate

pytestmark = pytest.mark.django_db

# ensure that when submissiondate field not available, Id10011 is used to determine date of submission
def test_submissiondate_logic():
    date1 = "2021-04-19T13:53:07.928Z"
    date2 = "2020-05-19T20:18:12.124+02:00"
    empty_string = "dk"

    va1 = VerbalAutopsy(submissiondate=date1)
    va2 = VerbalAutopsy(submissiondate=nan, Id10011=date2)
    va3 = VerbalAutopsy(submissiondate="", Id10011="")

    date_res_1 = get_submissiondate(va1, parse=True, empty_string=empty_string)
    date_res_2 = get_submissiondate(va2, parse=True, empty_string=empty_string)
    date_res_3 = get_submissiondate(va3, parse=True, empty_string=empty_string)

    assert date_res_1 == "2021-04-19"
    assert date_res_2 == "2020-05-19"
    assert date_res_3 == empty_string
