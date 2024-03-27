import io
import json
import zipfile

import pytest
from django.contrib.auth.models import Permission
from django.test import Client, RequestFactory

from va_explorer.tests.factories import (
    GroupFactory,
    LocationFactory,
    UserFactory,
    VerbalAutopsyFactory,
)
from va_explorer.users.models import User
from va_explorer.va_data_management.constants import REDACTED_STRING
from va_explorer.va_data_management.models import CauseOfDeath, Location, VerbalAutopsy
from va_explorer.va_export.forms import VADownloadForm

pytestmark = pytest.mark.django_db

CSV_ZIP_FILE_NAME = "export.csv.zip"
JSON_ZIP_FILE_NAME = "export.json.zip"
CSV_FILE_NAME = "va_download.csv"
JSON_FILE_NAME = "va_download.json"
FILE_CONTENT_TYPE = "application/zip"
POST_URL = "/va_export/verbalautopsy/"


def build_test_db():
    # Build locations
    province = LocationFactory.create()
    district1 = province.add_child(name="District1", location_type="district")
    facility_a = district1.add_child(
        name="Facility1",
        location_type="facility",
        key="facility_1",
        path_string=f"{province.name} Province/District1 District/Facility1",
    )
    district2 = province.add_child(name="District2", location_type="district")
    facility_b = district2.add_child(
        name="Facility1",
        location_type="facility",
        key="facility_1",
        path_string=f"{province.name} Province/District2 District/Facility1",
    )
    facility_c = district2.add_child(
        name="Facility2",
        location_type="facility",
        key="facility_2",
        path_string=f"{province.name} Province/District2 District/Facility2",
    )
    district2.add_child(
        name="Empty Facility",
        location_type="facility",
        key="empty",
        path_string=f"{province.name} Province/District2 District/Empty Facility",
    )

    # create VAs
    va1 = VerbalAutopsyFactory.create(location=facility_a, Id10023="2019-01-01")
    va2 = VerbalAutopsyFactory.create(location=facility_b, Id10023="2019-01-03")
    va3 = VerbalAutopsyFactory.create(location=facility_c, Id10023="2019-01-09")
    va4 = VerbalAutopsyFactory.create(location=facility_a, Id10023="2020-04-01")

    # Create CODs and assign to VAs
    CauseOfDeath.objects.create(cause="cod_b", settings={}, verbalautopsy=va1)
    CauseOfDeath.objects.create(cause="cod_a", settings={}, verbalautopsy=va2)
    CauseOfDeath.objects.create(cause="cod_b", settings={}, verbalautopsy=va3)
    CauseOfDeath.objects.create(cause="cod_a", settings={}, verbalautopsy=va4)

    # Build admin that can download data without location or PII restrictions
    can_download_data = Permission.objects.filter(codename="download_data").first()
    can_view_pii = Permission.objects.filter(codename="view_pii").first()

    admin_group = GroupFactory.create(permissions=[can_download_data, can_view_pii])
    non_admin_group = GroupFactory.create(permissions=[can_download_data])
    UserFactory.create(name="admin", groups=[admin_group])

    # build a non-admin user that can download but can't view pii
    UserFactory.create(name="no_pii", groups=[non_admin_group])


class TestAPIView:
    def test_csv_download(self, user: User):
        build_test_db()

        c = Client()
        c.force_login(user=user)

        response = c.post(POST_URL, data={"format": "csv"})
        assert response.status_code == 200

        # Django 3.2 has response.headers. For now, we'll access them per below
        # See https://docs.djangoproject.com/en/4.0/ref/request-response/#django.http.HttpResponse.headers
        assert response.headers["content-type"] == FILE_CONTENT_TYPE
        assert (
            response.headers["content-disposition"]
            == f"attachment; filename={CSV_ZIP_FILE_NAME}"
        )

        try:
            f = io.BytesIO(response.content)
            zipped_file = zipfile.ZipFile(f, "r")
            # Add one for the variable name header in the csv
            assert len(zipped_file.open(CSV_FILE_NAME).readlines()) == 5
        finally:
            zipped_file.close()
            f.close()

    def test_json_download(self, user: User):
        build_test_db()

        c = Client()
        c.force_login(user=user)

        response = c.post(POST_URL, data={"format": "json"})
        assert response.status_code == 200

        # Django 3.2 has response.headers. For now, we'll access them per below
        # See https://docs.djangoproject.com/en/4.0/ref/request-response/#django.http.HttpResponse.headers
        assert response.headers["content-type"] == FILE_CONTENT_TYPE
        assert (
            response.headers["content-disposition"]
            == f"attachment; filename={JSON_ZIP_FILE_NAME}"
        )

        try:
            f = io.BytesIO(response.content)
            zipped_file = zipfile.ZipFile(f, "r")

            json_data = json.loads(zipped_file.read(JSON_FILE_NAME))
            assert json_data["count"] == 4
        finally:
            zipped_file.close()
            f.close()

    def test_download_csv_with_no_matching_vas(self, user: User):
        build_test_db()
        # only download data from "No VA Facility", which will have no matching VAs
        no_va_facility = Location.objects.get(name="Empty Facility")

        c = Client()
        c.force_login(user=user)

        response = c.post(
            POST_URL, data={"format": "csv", "locations": no_va_facility.pk}
        )
        assert response.status_code == 200

        # Django 3.2 has response.headers. For now, we'll access them per below
        # See https://docs.djangoproject.com/en/4.0/ref/request-response/#django.http.HttpResponse.headers
        assert response.headers["content-type"] == FILE_CONTENT_TYPE
        assert (
            response.headers["content-disposition"]
            == f"attachment; filename={CSV_ZIP_FILE_NAME}"
        )

        try:
            f = io.BytesIO(response.content)
            zipped_file = zipfile.ZipFile(f, "r")
            # The single line is the variable name header in the csv
            assert len(zipped_file.open(CSV_FILE_NAME).readlines()) == 1
        finally:
            zipped_file.close()
            f.close()

    def test_download_json_with_no_matching_vas(self, user: User):
        build_test_db()
        # only download data from "No VA Facility", which will have no matching VAs
        no_va_facility = Location.objects.get(name="Empty Facility")

        c = Client()
        c.force_login(user=user)

        response = c.post(
            POST_URL, data={"format": "json", "locations": no_va_facility.pk}
        )
        assert response.status_code == 200

        # Django 3.2 has response.headers. For now, we'll access them per below
        # See https://docs.djangoproject.com/en/4.0/ref/request-response/#django.http.HttpResponse.headers
        assert response.headers["content-type"] == FILE_CONTENT_TYPE
        assert (
            response.headers["content-disposition"]
            == f"attachment; filename={JSON_ZIP_FILE_NAME}"
        )

        try:
            f = io.BytesIO(response.content)
            zipped_file = zipfile.ZipFile(f, "r")

            json_data = json.loads(zipped_file.read(JSON_FILE_NAME))
            assert json_data["count"] == 0
        finally:
            zipped_file.close()
            f.close()

    def test_location_filtering(self, user: User):
        build_test_db()
        # only download data from location a
        province = Location.objects.get(location_type="province")
        facility_1 = Location.objects.get(
            path_string=f"{province.name} Province/District1 District/Facility1"
        )

        c = Client()
        c.force_login(user=user)

        response = c.post(POST_URL, data={"format": "csv", "locations": facility_1.pk})
        assert response.status_code == 200

        # Django 3.2 has response.headers. For now, we'll access them per below
        # See https://docs.djangoproject.com/en/4.0/ref/request-response/#django.http.HttpResponse.headers
        assert response.headers["content-type"] == FILE_CONTENT_TYPE
        assert (
            response.headers["content-disposition"]
            == f"attachment; filename={CSV_ZIP_FILE_NAME}"
        )

        try:
            f = io.BytesIO(response.content)
            zipped_file = zipfile.ZipFile(f, "r")
            # Add one for the variable name header in the csv
            assert len(zipped_file.open(CSV_FILE_NAME).readlines()) == 3
        finally:
            zipped_file.close()
            f.close()

    def test_cod_filtering(self, user: User):
        build_test_db()
        # only download data from location a
        cod_name = "cod_a"

        c = Client()
        c.force_login(user=user)

        response = c.post(POST_URL, data={"format": "csv", "causes": cod_name})
        assert response.status_code == 200

        # Django 3.2 has response.headers. For now, we'll access them per below
        # See https://docs.djangoproject.com/en/4.0/ref/request-response/#django.http.HttpResponse.headers
        assert response.headers["content-type"] == FILE_CONTENT_TYPE
        assert (
            response.headers["content-disposition"]
            == f"attachment; filename={CSV_ZIP_FILE_NAME}"
        )

        try:
            f = io.BytesIO(response.content)
            zipped_file = zipfile.ZipFile(f, "r")
            # Add one for the variable name header in the csv
            assert len(zipped_file.open(CSV_FILE_NAME).readlines()) == 3
        finally:
            zipped_file.close()
            f.close()

    def test_time_filter(self, user: User):
        build_test_db()
        # only download data from location a
        start_date, end_date = "2020-01-01", "2021-01-01"

        c = Client()
        c.force_login(user=user)

        response = c.post(
            POST_URL,
            data={"format": "csv", "start_date": start_date, "end_date": end_date},
        )
        assert response.status_code == 200

        try:
            f = io.BytesIO(response.content)
            zipped_file = zipfile.ZipFile(f, "r")
            # Add one for the variable name header in the csv
            assert len(zipped_file.open(CSV_FILE_NAME).readlines()) == 2
        finally:
            zipped_file.close()
            f.close()

    def test_combined_filter_csv(self, user: User):
        build_test_db()
        # 1. Download from facility A after 1/1/2020 with COD_a in CSV format.
        # Assert only VA 4 is downloaded
        start_date = "2020-01-01"
        province = Location.objects.get(location_type="province")
        loc_a = Location.objects.get(
            path_string=f"{province.name} Province/District1 District/Facility1"
        )
        cod_name = "cod_a"

        query_data = {
            "format": "csv",
            "start_date": start_date,
            "locations": loc_a.pk,
            "causes": cod_name,
        }

        c = Client()
        c.force_login(user=user)

        response = c.post(POST_URL, data=query_data)
        assert response.status_code == 200

        # confirm correct number of VAs downloaded
        db_ct = VerbalAutopsy.objects.filter(
            Id10023__gte=start_date, causes__cause=cod_name, location__id=loc_a.pk
        ).count()

        try:
            f = io.BytesIO(response.content)
            zipped_file = zipfile.ZipFile(f, "r")
            # Add one for the variable name header in the csv
            assert len(zipped_file.open(CSV_FILE_NAME).readlines()) == db_ct + 1
        finally:
            zipped_file.close()
            f.close()

    def test_combined_filter_json(self, user: User):
        build_test_db()
        # 2. Download data from facility A from before 2020 with COD b in
        # JSON format. Assert only VA 1 is downloaded
        # NOTE: assumes records are stored in a wrapper with 'count' and 'record' keys.
        # If this structure changes, need to update this test

        end_date = "2020-01-01"
        province = Location.objects.get(location_type="province")
        loc_a = Location.objects.get(
            path_string=f"{province.name} Province/District1 District/Facility1"
        )
        cod_name = "cod_b"

        query_data = {
            "format": "json",
            "end_date": end_date,
            "locations": loc_a.pk,
            "causes": cod_name,
        }

        c = Client()
        c.force_login(user=user)

        # confirm correct number of VAs downloaded
        db_ct = VerbalAutopsy.objects.filter(
            Id10023__lte=end_date, causes__cause=cod_name, location__id=loc_a.pk
        ).count()

        response = c.post(POST_URL, data=query_data)
        assert response.status_code == 200

        # Django 3.2 has response.headers. For now, we'll access them per below
        # See https://docs.djangoproject.com/en/4.0/ref/request-response/#django.http.HttpResponse.headers
        assert response.headers["content-type"] == FILE_CONTENT_TYPE
        assert (
            response.headers["content-disposition"]
            == f"attachment; filename={JSON_ZIP_FILE_NAME}"
        )

        try:
            f = io.BytesIO(response.content)
            zipped_file = zipfile.ZipFile(f, "r")

            json_data = json.loads(zipped_file.read(JSON_FILE_NAME))
            assert json_data["count"] == db_ct
        finally:
            zipped_file.close()
            f.close()

        assert response.status_code == 200

    def test_redacted_download(self, rf: RequestFactory):
        build_test_db()
        user = User.objects.get(name="no_pii")

        c = Client()
        c.force_login(user=user)

        response = c.post(POST_URL, data={"format": "csv"})
        assert response.status_code == 200

        try:
            f = io.BytesIO(response.content)
            zipped_file = zipfile.ZipFile(f, "r")
            # Add one for the variable name header in the csv
            assert len(zipped_file.open(CSV_FILE_NAME).readlines()) == 5
            assert REDACTED_STRING in str(zipped_file.read(CSV_FILE_NAME))
        finally:
            zipped_file.close()
            f.close()

    def test_download_via_form(self, user: User):
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
