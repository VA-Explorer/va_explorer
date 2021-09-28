import pytest
from datetime import date, timedelta
from django.contrib.auth.models import Permission
from django.core.exceptions import PermissionDenied
from django.test import RequestFactory

from va_explorer.tests.factories import GroupFactory
from va_explorer.tests.factories import LocationFactory
from va_explorer.tests.factories import UserFactory
from va_explorer.tests.factories import VerbalAutopsyFactory
from va_explorer.va_analytics.views import dashboard_view
from va_explorer.va_analytics.views import user_supervision_view
from va_explorer.va_analytics.views import download_csv
from va_explorer.va_data_management.models import CauseOfDeath

pytestmark = pytest.mark.django_db


class TestDashboardView:
    def test_with_view_permission(self, rf: RequestFactory):
        can_view_dashboard = Permission.objects.filter(codename="view_dashboard").first()
        can_view_dashboard_group = GroupFactory.create(permissions=[can_view_dashboard])
        user = UserFactory.create(groups=[can_view_dashboard_group])

        request = rf.get("/va_analytics/dashboard/")
        request.user = user

        response = dashboard_view(request)

        assert response.status_code == 200

    def test_without_view_permission(self, rf: RequestFactory):
        no_permissions_group = GroupFactory.create(permissions=[])
        user = UserFactory.create(groups=[no_permissions_group])

        request = rf.get("/va_analytics/dashboard/")
        request.user = user

        with pytest.raises(PermissionDenied):
            dashboard_view(request)

class TestSupervisionView:
    def test_with_view_permission(self, rf: RequestFactory):
        can_supervise_users = Permission.objects.filter(codename="supervise_users").first()
        can_supervise_users_group = GroupFactory.create(permissions=[can_supervise_users])
        user = UserFactory.create(groups=[can_supervise_users_group])

        request = rf.get("/va_analytics/supervision/")
        request.user = user

        response = user_supervision_view(request)

        assert response.status_code == 200

    def test_without_view_permission(self, rf: RequestFactory):
        no_permissions_group = GroupFactory.create(permissions=[])
        user = UserFactory.create(groups=[no_permissions_group])

        request = rf.get("/va_analytics/supervision/")
        request.user = user

        with pytest.raises(PermissionDenied):
            user_supervision_view(request)

    def test_supervision_stats(self, rf: RequestFactory):
        can_supervise_users = Permission.objects.filter(codename="supervise_users").first()
        can_supervise_users_group = GroupFactory.create(permissions=[can_supervise_users])
        manager = UserFactory.create(groups=[can_supervise_users_group])

        # Build example data to 'supervise'
        province = LocationFactory.create()
        district1 = province.add_child(name='District1', location_type='district')
        facility1 = district1.add_child(name='Facility1', location_type='facility')
        field_worker = UserFactory.create(location_restrictions=[facility1])
        username = "field_worker"
        field_worker.set_va_username(username)
        va1 = VerbalAutopsyFactory.create(location=facility1, username=username, Id10010=username, submissiondate=str(date.today() - timedelta(days=8)))
        va2 = VerbalAutopsyFactory.create(location=facility1, username=username, Id10010=username, submissiondate=str(date.today()))

        request = rf.get("/va_analytics/supervision/")
        request.user = manager
        response = user_supervision_view(request)

        assert response.status_code == 200
        supervision_stats = response.context_data['supervision_stats'][0]
        assert supervision_stats['Total VAs'] == 2
        assert supervision_stats['Weeks of Data'] == 2
        assert supervision_stats['Last Submission'] == date.today()
        assert supervision_stats['VAs / week'] == 1.0


class TestDownloadCsvView:
    def test_download_with_permission(self, rf: RequestFactory):
        # Build locations
        province = LocationFactory.create()
        district1 = province.add_child(name='District1', location_type='district')
        facility1 = district1.add_child(name='Facility1', location_type='facility')
        district2 = province.add_child(name='District2', location_type='district')
        facility2 = district2.add_child(name='Facility2', location_type='facility')

        # Build user
        can_download_data = Permission.objects.filter(codename="download_data").first()
        can_download_data_group = GroupFactory.create(permissions=[can_download_data])
        user = UserFactory.create(groups=[can_download_data_group], location_restrictions=[district2])

        # One VA outside user's locations
        va1 = VerbalAutopsyFactory.create(location=facility1, Id10023="2019-01-01")

        cod = CauseOfDeath.objects.create(cause='va1 desc', settings={}, verbalautopsy=va1)

        # One VA in user's locations but with no cause
        VerbalAutopsyFactory.create(location=facility2)

        # One VA in user's locations with a cause (only one in the downloaded csv)
        va2 = VerbalAutopsyFactory.create(location=facility2, Id10023="2020-01-01")
        cod = CauseOfDeath.objects.create(cause='va2 desc', settings={}, verbalautopsy=va2)
        
        request = rf.get("/va_analytics/download")
        request.user = user

        response = download_csv(request)

        assert response.status_code == 200

        # 3 lines - header, va2, and blank line
        lines = response.content.decode('utf-8').split('\n')
        assert len(lines) == 3
        assert 'id,location' in lines[0]
        assert 'va2 desc' in lines[1]
        assert not lines[2]

    def test_download_without_permission(self, rf: RequestFactory):
        no_permissions_group = GroupFactory.create(permissions=[])
        user = UserFactory.create(groups=[no_permissions_group])

        request = rf.get("/va_analytics/download")
        request.user = user

        with pytest.raises(PermissionDenied):
            dashboard_view(request)

    def test_download_redacted_pii(self, rf: RequestFactory):
        # Build locations
        province = LocationFactory.create()
        district1 = province.add_child(name='District1', location_type='district')
        facility1 = district1.add_child(name='Facility1', location_type='facility')
        
        # Build user
        can_download_data = Permission.objects.filter(codename="download_data").first()
        can_download_data_group = GroupFactory.create(permissions=[can_download_data])
        user = UserFactory.create(groups=[can_download_data_group], location_restrictions=[district1])

        # Build verbal autopsy
        va1 = VerbalAutopsyFactory.create(location=facility1, Id10007='test', Id10023='2020-01-01')
        cod = CauseOfDeath.objects.create(cause='cause1', settings={}, verbalautopsy=va1)

        request = rf.get("/va_analytics/download")
        request.user = user

        response = download_csv(request)
        assert response.status_code == 200

        lines = response.content.decode('utf-8').split('\n')

        assert len(lines) == 3

        assert 'Id10007' in lines[0]
        assert 'Id10023' in lines[0]

        assert '** redacted **' in lines[1]

        assert 'test' not in lines[1]
        assert '2020-01-01' not in lines[1]
