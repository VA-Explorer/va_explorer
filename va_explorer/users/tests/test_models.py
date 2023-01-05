import pytest

from va_explorer.tests.factories import (
    LocationFactory,
    UserFactory,
    VerbalAutopsyFactory,
)
from va_explorer.users.models import User, UserPasswordHistory

pytestmark = pytest.mark.django_db


def test_user_get_absolute_url(user: User):
    assert user.get_absolute_url() == f"/users/{user.id}/"


def test_user_password_history_exists():
    user = UserFactory.create()
    user.set_password("test")
    user.save()

    password_history = UserPasswordHistory.objects.filter(user_id=user)
    assert password_history.count() == 1


def test_user_scoped_verbal_autopsies():
    # Set up a small tree of locations;
    # top level province, two districts, three facilities
    province = LocationFactory.create()
    district1 = province.add_child(name="District1", location_type="district")
    facility1 = district1.add_child(name="Facility1", location_type="facility")
    district2 = province.add_child(name="District2", location_type="district")
    facility2 = district2.add_child(name="Facility2", location_type="facility")
    facility3 = district2.add_child(name="Facility3", location_type="facility")
    # Each facility with one VA
    va1 = VerbalAutopsyFactory.create(location=facility1)
    va2 = VerbalAutopsyFactory.create(location=facility2)
    va3 = VerbalAutopsyFactory.create(location=facility3)
    # A user with no location restrictions should see all VAs in the system
    user = UserFactory.create()
    assert user.verbal_autopsies().count() == 3
    # A user restricted to the province should see all VAs
    user = UserFactory.create(location_restrictions=[province])
    assert user.verbal_autopsies().count() == 3
    # A user restricted to a district should see the correct subset of VAs
    user = UserFactory.create(location_restrictions=[district1])
    assert user.verbal_autopsies().count() == 1
    assert va1 in user.verbal_autopsies()
    user = UserFactory.create(location_restrictions=[district2])
    assert user.verbal_autopsies().count() == 2
    assert va2 in user.verbal_autopsies()
    assert va3 in user.verbal_autopsies()
    # A user restricted to a facility should see the correct VA
    user = UserFactory.create(location_restrictions=[facility1])
    assert user.verbal_autopsies().count() == 1
    assert va1 in user.verbal_autopsies()
    user = UserFactory.create(location_restrictions=[facility2])
    assert user.verbal_autopsies().count() == 1
    assert va2 in user.verbal_autopsies()
    user = UserFactory.create(location_restrictions=[facility3])
    assert user.verbal_autopsies().count() == 1
    assert va3 in user.verbal_autopsies()
