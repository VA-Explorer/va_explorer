import json
from io import BytesIO
from urllib.parse import urlencode

import pandas as pd
import pytest
from django.contrib.auth.models import Permission
from django.test import RequestFactory
from django.urls import reverse

from va_explorer.tests.factories import (
    GroupFactory,
    LocationFactory,
    UserFactory,
    VerbalAutopsyFactory,
)
from va_explorer.users.models import User
from va_explorer.va_data_management.models import (
    REDACTED_STRING,
    CauseOfDeath,
    Location,
    VerbalAutopsy,
)
from va_explorer.va_export.forms import VADownloadForm
from va_explorer.va_export.views import va_api_view

pytestmark = pytest.mark.django_db


def build_test_db():

    # Build locations
    province = LocationFactory.create()
    district1 = province.add_child(name="District1", location_type="district")
    facility_a = district1.add_child(name="Facility1", location_type="facility")
    district2 = province.add_child(name="District2", location_type="district")
    facility_b = district2.add_child(name="Facility2", location_type="facility")
    facility_c = district2.add_child(name="Facility2", location_type="facility")

    # create VAs
    va1 = VerbalAutopsyFactory.create(location=facility_a, Id10023="2019-01-01")
    va2 = VerbalAutopsyFactory.create(location=facility_b, Id10023="2019-01-03")
    va3 = VerbalAutopsyFactory.create(location=facility_c, Id10023="2019-01-09")
    va4 = VerbalAutopsyFactory.create(location=facility_a, Id10023="2020-04-01")

    # Create CODs and assign to VAs
    cod1 = CauseOfDeath.objects.create(cause="cod_b", settings={}, verbalautopsy=va1)
    cod2 = CauseOfDeath.objects.create(cause="cod_a", settings={}, verbalautopsy=va2)
    cod3 = CauseOfDeath.objects.create(cause="cod_b", settings={}, verbalautopsy=va3)
    cod4 = CauseOfDeath.objects.create(cause="cod_a", settings={}, verbalautopsy=va4)

    # Build admin that can download data without location or PII restrictions
    can_download_data = Permission.objects.filter(codename="download_data").first()
    can_view_pii = Permission.objects.filter(codename="view_pii").first()

    admin_group = GroupFactory.create(permissions=[can_download_data, can_view_pii])
    non_admin_group = GroupFactory.create(permissions=[can_download_data])
    user = UserFactory.create(name="admin", groups=[admin_group])

    # build a non-admin user that can download but can't view pii
    user_no_pii = UserFactory.create(name="no_pii", groups=[non_admin_group])


class TestAPIView:
    def test_csv_download(self, rf: RequestFactory):
        build_test_db()
        request = rf.get("/va_export/verbalautopsy/?format=csv")
        request.user = User.objects.get(name="admin")
        response = va_api_view(request)

        assert response.status_code == 200
        # confirm response content has some data
        assert len(response.content) > 0
        df = pd.read_csv(BytesIO(response.content))
        # confirm that all data was downloaded
        db_va_ct = VerbalAutopsy.objects.count()
        download_ct = df.shape[0]
        assert download_ct == db_va_ct

    def test_json_download(self, rf: RequestFactory):
        build_test_db()
        request = rf.get("/va_export/verbalautopsy/?format=json")
        request.user = User.objects.get(name="admin")
        response = va_api_view(request)

        assert response.status_code == 200
        # confirm response content has some data
        assert len(response.content) > 0

        json_data = json.loads(response.content)
        # confirm that all data was downloaded
        db_va_ct = VerbalAutopsy.objects.count()
        # NOTE: assumes records are stored in a wrapper with 'count' and 'record' keys.
        # If this structure changes, need to update this test
        download_ct = json_data["count"]
        assert download_ct == db_va_ct

    def test_location_filtering(self, rf: RequestFactory):
        build_test_db()
        # only download data from location a
        loc_a = Location.objects.get(name="Facility1")

        request = rf.get(f"/va_export/verbalautopsy/?format=csv&locations={loc_a.pk}")
        request.user = User.objects.get(name="admin")
        response = va_api_view(request)

        assert response.status_code == 200
        # confirm response content has some data
        assert len(response.content) > 0
        # confirm only 2/4 vas were downoaded
        df = pd.read_csv(BytesIO(response.content))
        download_ct = df.shape[0]
        db_ct = VerbalAutopsy.objects.filter(location__id=loc_a.pk).count()
        assert download_ct == db_ct
        # confirm only from location a
        uniq_loc = df["location"].unique().tolist()
        assert (len(uniq_loc) == 1) and (uniq_loc[0] == loc_a.name)

    def test_cod_filtering(self, rf: RequestFactory):
        build_test_db()
        # only download data from location a
        cod_name = "cod_a"

        request = rf.get(f"/va_export/verbalautopsy/?format=csv&causes={cod_name}")
        request.user = User.objects.get(name="admin")
        response = va_api_view(request)

        assert response.status_code == 200
        # confirm response content has some data
        assert len(response.content) > 0
        # confirm the right number of VAs were downloaded
        df = pd.read_csv(BytesIO(response.content))
        download_ct = df.shape[0]
        db_ct = VerbalAutopsy.objects.filter(causes__cause=cod_name).count()
        assert download_ct == db_ct
        # confirm all VAs have cause cod_a
        uniq_cod = df["cause"].unique().tolist()
        assert (len(uniq_cod) == 1) and (uniq_cod[0] == cod_name)

    def test_time_filter(self, rf: RequestFactory):
        build_test_db()
        # only download data from location a
        start_date, end_date = "2020-01-01", "2021-01-01"

        request = rf.get(
            f"/va_export/verbalautopsy/?format=csv&start_date={start_date}&end_date={end_date}"
        )
        request.user = User.objects.get(name="admin")
        response = va_api_view(request)

        assert response.status_code == 200
        # confirm response content has some data
        assert len(response.content) > 0
        df = pd.read_csv(BytesIO(response.content))
        # confirm only 1 VA was downloaded
        download_ct = df.shape[0]
        # assumes filtering is done by date of death (Id10023). If that changes, need to update fields below
        db_ct = VerbalAutopsy.objects.filter(
            Id10023__gte=start_date, Id10023__lte=end_date
        ).count()
        assert download_ct == db_ct
        # confirm all VAs are within chosen time period
        assert (
            (df["Id10023"] >= start_date) & (df["Id10023"] <= end_date)
        ).sum() == db_ct

    def test_combined_filter_csv(self, rf: RequestFactory):
        build_test_db()
        # 1. Download from facility A after 1/1/2020 with COD_a in CSV format. Assert only VA 4 is downloaded
        start_date = "2020-01-01"
        loc_a = Location.objects.get(name="Facility1")
        cod_name = "cod_a"
        comb_csv_query = (
            f"format=csv&start_date={start_date}&locations={loc_a.pk}&causes={cod_name}"
        )
        request = rf.get(f"/va_export/verbalautopsy/?{comb_csv_query}")
        request.user = User.objects.get(name="admin")
        response = va_api_view(request)

        assert response.status_code == 200
        # confirm correct number of VAs downloaded
        db_ct = VerbalAutopsy.objects.filter(
            Id10023__gte=start_date, causes__cause=cod_name, location__id=loc_a.pk
        ).count()
        df = pd.read_csv(BytesIO(response.content))
        download_ct = df.shape[0]
        assert download_ct == db_ct
        # confirm all VAs are within chosen time period
        assert (df["Id10023"] >= start_date).sum() == db_ct
        # confirm all VAs have cause cod_a
        uniq_cod = df["cause"].unique().tolist()
        assert (len(uniq_cod) == 1) and (uniq_cod[0] == cod_name)
        # confirm all VAs are from location a
        uniq_loc = df["location"].unique().tolist()
        assert (len(uniq_loc) == 1) and (uniq_loc[0] == loc_a.name)

    def test_combined_filter_json(self, rf: RequestFactory):
        build_test_db()
        # 2. Download data from facility A from before 2020 with COD b in JSON format. Assert only VA 1 is downloaded
        # NOTE: assumes records are stored in a wrapper with 'count' and 'record' keys.
        # If this structure changes, need to update this test

        end_date = "2020-01-01"
        loc_a = Location.objects.get(name="Facility1")
        cod_name = "cod_b"
        comb_csv_query = (
            f"format=json&end_date={end_date}&locations={loc_a.pk}&causes={cod_name}"
        )
        request = rf.get(f"/va_export/verbalautopsy/?{comb_csv_query}")
        request.user = User.objects.get(name="admin")
        response = va_api_view(request)

        assert response.status_code == 200
        # confirm correct number of VAs downloaded
        db_ct = VerbalAutopsy.objects.filter(
            Id10023__lte=end_date, causes__cause=cod_name, location__id=loc_a.pk
        ).count()
        json_obj = json.loads(response.content)
        download_ct = json_obj["count"]
        assert download_ct == db_ct
        # confirm all VAs are within chosen time period
        df = pd.read_json(json_obj["records"])
        assert (df["Id10023"] <= end_date).sum() == db_ct
        # confirm all VAs have cause cod_a
        uniq_cod = df["cause"].unique().tolist()
        assert (len(uniq_cod) == 1) and (uniq_cod[0] == cod_name)
        # confirm all VAs are from location a
        uniq_loc = df["location"].unique().tolist()
        assert (len(uniq_loc) == 1) and (uniq_loc[0] == loc_a.name)

    def test_redacted_download(self, rf: RequestFactory):
        build_test_db()
        request = rf.get("/va_export/verbalautopsy/?format=csv")
        request.user = User.objects.get(name="no_pii")
        response = va_api_view(request)

        assert response.status_code == 200
        # confirm redacted string appearing in records
        assert REDACTED_STRING in str(response.content)
        # confirm all records are included in download
        df = pd.read_csv(BytesIO(response.content))
        assert VerbalAutopsy.objects.count() == df.shape[0]

    def test_download_via_form(self, rf: RequestFactory):
        build_test_db()
        # filter by id of last location in test db
        loc_id = Location.objects.last().pk
        download_form = VADownloadForm(
            {
                "action": "download",
                "format": "csv",
                "end_date": "2020-01-01",
                "location": str(loc_id),
            }
        )

        assert download_form.is_valid()

        form_data = download_form.cleaned_data
        api_url = reverse("va_export:va_api") + "?" + urlencode(form_data)
        request = rf.get(api_url)
        request.user = User.objects.get(name="admin")
        response = va_api_view(request)
        df = pd.read_csv(BytesIO(response.content))
        # result should be a subset of all data
        assert df.shape[0] < VerbalAutopsy.objects.count()
