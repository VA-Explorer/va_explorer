import pytest
from django.contrib.auth.models import Permission
from django.test import Client

from va_explorer.tests.factories import (
    FacilityFactory,
    FieldWorkerFactory,
    FieldWorkerGroupFactory,
    GroupFactory,
    LocationFactory,
    UserFactory,
    VaUsernameFactory,
    VerbalAutopsyFactory,
)
from va_explorer.users.models import User
from va_explorer.va_data_management.models import REDACTED_STRING, VerbalAutopsy

pytestmark = pytest.mark.django_db


# Get the index and make sure the VA in the system is listed
def test_index_with_valid_permission(user: User):
    can_view_record = Permission.objects.filter(codename="view_verbalautopsy").first()
    can_view_pii = Permission.objects.filter(codename="view_pii").first()
    can_view_record_group = GroupFactory.create(
        permissions=[can_view_record, can_view_pii]
    )
    user = UserFactory.create(groups=[can_view_record_group])
    client = Client()
    client.force_login(user=user)
    va = VerbalAutopsyFactory.create(Id10017="Victim name", Id10010="Interviewer name")
    response = client.get("/va_data_management/")
    assert response.status_code == 200
    assert bytes(va.Id10010, "utf-8") in response.content


# Get the index and make sure the VA in the system is listed
def test_index_redacted(user: User):
    can_view_record = Permission.objects.filter(codename="view_verbalautopsy").first()
    can_view_record_group = GroupFactory.create(permissions=[can_view_record])
    user = UserFactory.create(groups=[can_view_record_group])

    client = Client()
    client.force_login(user=user)
    va = VerbalAutopsyFactory.create(Id10023="death date")
    response = client.get("/va_data_management/")
    assert response.status_code == 200
    assert bytes(REDACTED_STRING, "utf-8") in response.content
    assert bytes(va.Id10023, "utf-8") not in response.content


# Request the index without permissions and make sure its forbidden
def test_index_without_valid_permission(user: User):
    client = Client()
    client.force_login(user=user)

    response = client.get("/va_data_management/")
    assert response.status_code == 403


# Show a VA and make sure the data is as expected
def test_show(user: User):
    can_view_record = Permission.objects.filter(codename="view_verbalautopsy").first()
    can_view_pii = Permission.objects.filter(codename="view_pii").first()
    can_view_record_group = GroupFactory.create(
        permissions=[can_view_record, can_view_pii]
    )
    user = UserFactory.create(groups=[can_view_record_group])

    client = Client()
    client.force_login(user=user)
    va = VerbalAutopsyFactory.create(Id10017="Victim name")
    response = client.get(f"/va_data_management/show/{va.id}")
    assert response.status_code == 200
    assert bytes(va.Id10017, "utf-8") in response.content


# Show a VA and make sure the data is as expected (with redacted)
def test_show_redacted(user: User):
    can_view_record = Permission.objects.filter(codename="view_verbalautopsy").first()
    can_view_record_group = GroupFactory.create(permissions=[can_view_record])
    user = UserFactory.create(groups=[can_view_record_group])

    client = Client()
    client.force_login(user=user)
    va = VerbalAutopsyFactory.create(Id10017="Victim name")
    response = client.get(f"/va_data_management/show/{va.id}")
    assert response.status_code == 200
    assert bytes(REDACTED_STRING, "utf-8") in response.content
    assert bytes(va.Id10017, "utf-8") not in response.content


# Request the show page for VA without permissions and make sure it's forbidden
def test_show_without_valid_permissions(user: User):
    client = Client()
    client.force_login(user=user)
    va = VerbalAutopsyFactory.create(Id10017="Victim name", Id10010="Interviewer name")
    response = client.get(f"/va_data_management/show/{va.id}")
    assert response.status_code == 403


# Request the edit form of a VA and make sure the data is as expected
def test_edit_with_valid_permissions(user: User):
    can_edit_record = Permission.objects.filter(codename="change_verbalautopsy").first()
    can_view_pii = Permission.objects.filter(codename="view_pii").first()
    can_edit_record_group = GroupFactory.create(
        permissions=[can_edit_record, can_view_pii]
    )
    user = UserFactory.create(groups=[can_edit_record_group])

    client = Client()
    client.force_login(user=user)

    va = VerbalAutopsyFactory.create(Id10017="Victim name", Id10010="Interviewer name")
    response = client.get(f"/va_data_management/edit/{va.id}")
    assert response.status_code == 200
    assert bytes(va.Id10010, "utf-8") in response.content
    assert bytes(va.Id10017, "utf-8") in response.content


# Request the edit form of a VA without permissions and make sure its forbidden
def test_edit_without_valid_permissions(user: User):
    client = Client()
    client.force_login(user=user)

    va = VerbalAutopsyFactory.create(Id10017="Victim name", Id10010="Interviewer name")
    response = client.get(f"/va_data_management/edit/{va.id}")
    assert response.status_code == 403


# Update a VA and make sure 1) the data is changed and 2) the history is tracked
def test_save_with_valid_permissions(user: User):
    can_edit_record = Permission.objects.filter(codename="change_verbalautopsy").first()
    can_view_record = Permission.objects.filter(codename="view_verbalautopsy").first()
    can_view_pii = Permission.objects.filter(codename="view_pii").first()
    can_edit_view_record_group = GroupFactory.create(
        permissions=[can_edit_record, can_view_record, can_view_pii]
    )
    user = UserFactory.create(groups=[can_edit_view_record_group])

    client = Client()
    client.force_login(user=user)
    va = VerbalAutopsyFactory.create(Id10017="Victim name", Id10010="Interviewer name")
    assert va.history.count() == 1
    new_name = "Updated Example Name"
    response = client.post(
        f"/va_data_management/edit/{va.id}",
        {"Id10010": new_name, "Id10023": "2021-03-01", "Id10058": va.location.name},
    )
    assert response.status_code == 302
    assert response["Location"] == f"/va_data_management/show/{va.id}"
    va = VerbalAutopsy.objects.get(id=va.id)
    assert va.Id10010 == new_name
    assert va.Id10023 == "2021-03-01"
    assert va.history.count() == 2
    assert va.history.first().history_user == user
    response = client.get(f"/va_data_management/show/{va.id}")
    # TODO: We need to handle timezones correctly
    assert (
        bytes(va.history.first().history_date.strftime("%Y-%m-%d %H:%M"), "utf-8")
        in response.content
    )
    assert bytes(va.history.first().history_user.name, "utf-8") in response.content


# Update a VA and make sure there is no redirect, TODO check form.errors or create separate form test to make this more accurate
def test_save_with_invalid_date_format(user: User):
    can_edit_record = Permission.objects.filter(codename="change_verbalautopsy").first()
    can_view_record = Permission.objects.filter(codename="view_verbalautopsy").first()
    can_view_pii = Permission.objects.filter(codename="view_pii").first()
    can_edit_view_record_group = GroupFactory.create(
        permissions=[can_edit_record, can_view_record, can_view_pii]
    )
    user = UserFactory.create(groups=[can_edit_view_record_group])

    client = Client()
    client.force_login(user=user)
    va = VerbalAutopsyFactory.create(Id10017="Victim name", Id10010="Interviewer name")
    assert va.history.count() == 1
    new_name = "Updated Example Name"
    response = client.post(
        f"/va_data_management/edit/{va.id}",
        {"Id10010": new_name, "Id10023": "this is not a date 1234"},
    )
    assert response.status_code == 200


# Verify save access is restricted
def test_save_without_valid_permissions(user: User):
    client = Client()
    client.force_login(user=user)
    va = VerbalAutopsyFactory.create(Id10017="Victim name", Id10010="Interviewer name")
    assert va.history.count() == 1
    new_name = "Updated Example Name"
    location = va.location
    response = client.post(f"/va_data_management/edit/{va.id}", {"Id10010": new_name})
    assert response.status_code == 403


# Reset an updated VA and make sure 1) the data is reset to original values and 2) the history is tracked
def test_reset_with_valid_permissions(user: User):
    can_edit_record = Permission.objects.filter(codename="change_verbalautopsy").first()
    can_view_pii = Permission.objects.filter(codename="view_pii").first()
    can_edit_record_group = GroupFactory.create(
        permissions=[can_edit_record, can_view_pii]
    )
    user = UserFactory.create(groups=[can_edit_record_group])

    client = Client()
    client.force_login(user=user)
    va = VerbalAutopsyFactory.create(Id10017="Victim name", Id10010="Interviewer name")
    original_name = va.Id10010
    original_dod = va.Id10023
    new_name = "Updated Name"
    client.post(
        f"/va_data_management/edit/{va.id}",
        {"Id10010": new_name, "Id10023": "2021-03-01", "Id10058": va.location.name},
    )
    va = VerbalAutopsy.objects.get(id=va.id)
    assert va.Id10010 == new_name
    assert va.history.count() == 2
    # TODO: Switch the buttons to forms in show.html and make this a POST.
    response = client.get(f"/va_data_management/reset/{va.id}")
    assert response.status_code == 302
    assert response["Location"] == f"/va_data_management/show/{va.id}"
    va = VerbalAutopsy.objects.get(id=va.id)
    assert va.Id10010 == original_name
    assert va.Id10023 == original_dod
    assert va.history.count() == 3
    assert va.history.first().history_user == user


# Verify reset access is restricted
def test_reset_without_valid_permissions(user: User):
    client = Client()
    client.force_login(user=user)
    va = VerbalAutopsyFactory.create(Id10017="Victim name", Id10010="Interviewer name")
    response = client.get(f"/va_data_management/reset/{va.id}")
    assert response.status_code == 403


# Revert an updated VA and make sure 1) the data is reset to previous version and 2) the history is tracked
def test_revert_latest_with_valid_permissions(user: User):
    can_edit_record = Permission.objects.filter(codename="change_verbalautopsy").first()
    can_view_pii = Permission.objects.filter(codename="view_pii").first()
    can_edit_record_group = GroupFactory.create(
        permissions=[can_edit_record, can_view_pii]
    )
    user = UserFactory.create(groups=[can_edit_record_group])

    client = Client()
    client.force_login(user=user)
    va = VerbalAutopsyFactory.create(Id10017="Victim name", Id10010="Interviewer name")
    original_name = va.Id10010
    second_name = "Second Name"
    third_name = "Third Name"
    client.post(
        f"/va_data_management/edit/{va.id}",
        {"Id10010": second_name, "Id10023": "2021-03-01", "Id10058": va.location.name},
    )
    va = VerbalAutopsy.objects.get(id=va.id)
    assert va.Id10010 == second_name
    assert va.Id10023 == "2021-03-01"
    assert va.history.count() == 2
    client.post(
        f"/va_data_management/edit/{va.id}",
        {"Id10010": third_name, "Id10023": "2021-03-02", "Id10058": va.location.name},
    )
    va = VerbalAutopsy.objects.get(id=va.id)
    assert va.Id10010 == third_name
    assert va.Id10023 == "2021-03-02"
    assert va.history.count() == 3
    # TODO: Switch the buttons to forms in show.html and make this a POST.
    response = client.get(f"/va_data_management/revert_latest/{va.id}")
    assert response.status_code == 302
    assert response["Location"] == f"/va_data_management/show/{va.id}"
    va = VerbalAutopsy.objects.get(id=va.id)
    assert va.Id10010 == second_name
    assert va.Id10023 == "2021-03-01"
    assert va.history.count() == 4
    assert va.history.first().history_user == user


# Verify revert access is restricted
def test_revert_latest_without_valid_permissions(user: User):
    client = Client()
    client.force_login(user=user)
    va = VerbalAutopsyFactory.create(Id10017="Victim name", Id10010="Interviewer name")
    response = client.get(f"/va_data_management/revert_latest/{va.id}")
    assert response.status_code == 403


# Test all methods for access control restrictions
def test_access_control(user: User):
    # Set up a location tree so the user can be scoped without access to a VA
    can_edit_record = Permission.objects.filter(codename="change_verbalautopsy").first()
    can_edit_record_group = GroupFactory.create(permissions=[can_edit_record])
    can_view_record = Permission.objects.filter(codename="view_verbalautopsy").first()
    can_view_record_group = GroupFactory.create(permissions=[can_view_record])
    user = UserFactory.create(groups=[can_edit_record_group, can_view_record_group])

    province = LocationFactory.create()
    district1 = province.add_child(name="District1", location_type="district")
    district2 = province.add_child(name="District2", location_type="district")
    facility = district1.add_child(name="Facility", location_type="facility")
    va = VerbalAutopsyFactory.create(location=facility, Id10023="death date")
    user.location_restrictions.set([district2])  # Should not have access to VA
    client = Client()
    client.force_login(user=user)
    response = client.get("/va_data_management/")
    assert response.status_code == 200
    assert bytes(va.Id10023, "utf-8") not in response.content
    response = client.get(f"/va_data_management/show/{va.id}")
    assert response.status_code == 404
    response = client.get(f"/va_data_management/edit/{va.id}")
    assert response.status_code == 404
    response = client.post(
        f"/va_data_management/edit/{va.id}", {"10023": "new death date"}
    )
    assert response.status_code == 404
    response = client.get(f"/va_data_management/reset/{va.id}")
    assert response.status_code == 404
    response = client.get(f"/va_data_management/revert_latest/{va.id}")
    assert response.status_code == 404


# A Field Worker can access only the Verbal Autopsies they create through the username on the Verbal Autopsy
def test_field_worker_access_control():
    can_view_record = Permission.objects.filter(codename="view_verbalautopsy").first()
    can_view_pii = Permission.objects.filter(codename="view_pii").first()
    field_worker_group = FieldWorkerGroupFactory.create(
        permissions=[can_view_record, can_view_pii]
    )
    field_worker = FieldWorkerFactory.create(groups=[field_worker_group])
    field_worker_username = VaUsernameFactory.create(user=field_worker)

    facility = FacilityFactory.create()
    field_worker.location_restrictions.add(*[facility])

    field_worker.save()
    field_worker_username.save()

    va = VerbalAutopsyFactory.create(
        Id10017="deceased_name_1",
        Id10010="Role specific value",
        location=facility,
        username=field_worker_username.va_username,
    )
    va2 = VerbalAutopsyFactory.create(
        Id10017="deceased_name_2", location=facility, username=""
    )

    client = Client()
    client.force_login(user=field_worker)

    response = client.get("/va_data_management/")
    assert response.status_code == 200
    assert str(va.Id10017).encode("utf_8") in response.content
    assert (
        str(va.Id10010).encode("utf_8") not in response.content
    )  # field workers see deceased, not interviewer
    assert str(va2.Id10017).encode("utf_8") not in response.content

    response = client.get(f"/va_data_management/show/{va.id}")
    assert response.status_code == 200

    response = client.get(f"/va_data_management/show/{va2.id}")
    assert response.status_code == 404
