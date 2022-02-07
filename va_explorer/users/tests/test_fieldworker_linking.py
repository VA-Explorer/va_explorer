import pytest
from django.contrib.auth.models import Group

from va_explorer.tests.factories import UserFactory, VerbalAutopsyFactory
from va_explorer.users.models import User
from va_explorer.users.tests.user_test_utils import setup_test_db
from va_explorer.users.utils.field_worker_linking import (
    assign_va_usernames,
    link_fieldworkers_to_vas,
)
from va_explorer.va_data_management.models import Location, VerbalAutopsy

pytestmark = pytest.mark.django_db


def test_link_fieldworkers_to_vas():
    setup_test_db(with_vas=False)
    # Location gets assigned automatically/randomly.
    # If that changes in loading.py we'll need to change that here too.
    # create users before VAs are added to system
    group, _ = Group.objects.get_or_create(name="Field Workers")
    UserFactory(name="Johnny", email="field_worker_1@example.com", groups=[group]).save()
    UserFactory(name="Apple", email="field_worker_2@example.com", groups=[group]).save()
    UserFactory(name="Seed", email="field_worker_3@example.com", groups=[group]).save()

    worker_emails = list(User.objects.values_list("email", flat=True))

    loc1 = Location.objects.filter(name="Facility1").first()
    loc2 = Location.objects.filter(name="Facility2").first()

    # add VA data to system
    VerbalAutopsyFactory.create(Id10010="unknown_user", location=loc1).save()
    VerbalAutopsyFactory.create(Id10010="Johnny", location=loc2).save()
    VerbalAutopsyFactory.create(Id10010="appLe", location=loc1).save()
    VerbalAutopsyFactory.create(Id10010="SEED", location=loc2).save()

    res = link_fieldworkers_to_vas(emails=worker_emails)
    res = set(res)
    assert len(res) == 3
    assert ("johnny", "johnny") in res
    assert ("apple", "apple") in res
    assert ("seed", "seed") in res

    usernames = [u.get_va_username() for u in User.objects.all()]
    assert len(set(usernames).intersection({"johnny", "apple", "seed"})) == 3

    va_usernames = VerbalAutopsy.objects.values_list("username", flat=True)
    assert len(set(va_usernames).intersection({"johnny", "apple", "seed"})) == 3

    unknown = VerbalAutopsy.objects.filter(Id10010="unknown_user").first()
    assert unknown
    assert len(unknown.username) == 0


def test_assign_va_usernames():
    setup_test_db(with_vas=False)
    # dummy facilities
    loc1 = Location.objects.filter(name="Facility1").first()
    loc2 = Location.objects.filter(name="Facility2").first()

    # first, create VAs
    VerbalAutopsyFactory.create(instanceid="instance1", Id10010="johnny", location=loc1).save()
    VerbalAutopsyFactory.create(instanceid="instance2", Id10010="Johnny", location=loc2).save()
    VerbalAutopsyFactory.create(instanceid="instance3", Id10010="appLe", location=loc1).save()
    VerbalAutopsyFactory.create(instanceid="instance4", Id10010="SEED", location=loc2).save()
    VerbalAutopsyFactory.create(instanceid="instance5", Id10010="JOHNNY", location=loc2).save()

    # then, create a field worker johnny
    group, _ = Group.objects.get_or_create(name="Field Workers")
    u1 = UserFactory(name="Johnny", email="field_worker_1@example.com", groups=[group])
    u1.set_va_username("johnny")
    u1.save()

    # finally, match vas against field workers
    success_ct = assign_va_usernames(usernames="johnny")
    assert success_ct == 3
    assert VerbalAutopsy.objects.get(instanceid="instance1").username == "johnny"
    assert VerbalAutopsy.objects.get(instanceid="instance2").username == "johnny"
    assert VerbalAutopsy.objects.get(instanceid="instance3").username != "johnny"
    assert VerbalAutopsy.objects.get(instanceid="instance4").username != "johnny"
    assert VerbalAutopsy.objects.get(instanceid="instance5").username == "johnny"
