import pytest
from django.contrib.auth.models import Permission
from django.core.exceptions import PermissionDenied
from django.test import RequestFactory

from va_explorer.tests.factories import GroupFactory, UserFactory
from va_explorer.va_analytics.views import (
    dashboard_view, download_csv,
)

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


# Note: Downloading the dashboard requires view_dashboard permission at the moment.
class TestDownloadDashboardCsvView:
    def test_donwload_with_permission(self, rf: RequestFactory):
        can_view_dashboard = Permission.objects.filter(codename="view_dashboard").first()
        can_view_dashboard_group = GroupFactory.create(permissions=[can_view_dashboard])
        user = UserFactory.create(groups=[can_view_dashboard_group])

        request = rf.get("/va_analytics/download")
        request.user = user

        response = download_csv(request)

        assert response.status_code == 200

    def test_download_without_permission(self, rf: RequestFactory):
        no_permissions_group = GroupFactory.create(permissions=[])
        user = UserFactory.create(groups=[no_permissions_group])

        request = rf.get("/va_analytics/download")
        request.user = user

        with pytest.raises(PermissionDenied):
            dashboard_view(request)
