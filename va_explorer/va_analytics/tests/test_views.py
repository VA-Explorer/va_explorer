from datetime import date, timedelta

import pytest
from django.contrib.auth.models import Permission
from django.core.exceptions import PermissionDenied
from django.test import RequestFactory

from va_explorer.tests.factories import (
    GroupFactory,
    LocationFactory,
    UserFactory,
    VerbalAutopsyFactory,
)
from va_explorer.va_analytics.views import dashboard_view, user_supervision_view

pytestmark = pytest.mark.django_db


class TestDashboardView:
    def test_with_view_permission(self, rf: RequestFactory):
        can_view_dashboard = Permission.objects.filter(
            codename="view_dashboard"
        ).first()
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
        can_supervise_users = Permission.objects.filter(
            codename="supervise_users"
        ).first()
        can_supervise_users_group = GroupFactory.create(
            permissions=[can_supervise_users]
        )
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
        can_supervise_users = Permission.objects.filter(
            codename="supervise_users"
        ).first()
        can_supervise_users_group = GroupFactory.create(
            permissions=[can_supervise_users]
        )
        manager = UserFactory.create(groups=[can_supervise_users_group])

        # Build example data to 'supervise'
        province = LocationFactory.create()
        district1 = province.add_child(name="District1", location_type="district")
        facility1 = district1.add_child(name="Facility1", location_type="facility")
        UserFactory.create(location_restrictions=[facility1])
        username = "field_worker"
        VerbalAutopsyFactory.create(
            location=facility1,
            Id10010=username,
            Id10012=str(date.today() - timedelta(days=8)),
        )
        VerbalAutopsyFactory.create(
            location=facility1,
            Id10010=username,
            Id10012=str(date.today()),
        )

        request = rf.get("/va_analytics/supervision/")
        request.user = manager
        response = user_supervision_view(request)

        assert response.status_code == 200
        supervision_stats = response.context_data["supervision_stats"][0]
        assert supervision_stats["Total VAs"] == 2
        assert supervision_stats["Weeks of Data"] == 2
        assert supervision_stats["Last Interview"] == date.today()
        assert supervision_stats["VAs / week"] == 1.0
