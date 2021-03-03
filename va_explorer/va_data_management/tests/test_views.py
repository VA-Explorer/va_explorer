import pytest
from django.test import Client
from django.contrib.auth.models import Permission
from va_explorer.users.models import User
from va_explorer.va_data_management.models import VerbalAutopsy
from va_explorer.tests.factories import GroupFactory, VerbalAutopsyFactory, UserFactory, LocationFactory

pytestmark = pytest.mark.django_db


# Get the index and make sure the VA in the system is listed
def test_index_with_valid_permission(user: User):
    can_view_record = Permission.objects.filter(codename="view_verbalautopsy").first()
    can_view_record_group = GroupFactory.create(permissions=[can_view_record])
    user = UserFactory.create(groups=[can_view_record_group])

    client = Client()
    client.force_login(user=user)
    va = VerbalAutopsyFactory.create()
    response = client.get("/va_data_management/")
    assert response.status_code == 200
    assert bytes(va.Id10007, "utf-8") in response.content


# Request the index without permissions and make sure its forbidden
def test_index_without_valid_permission(user: User):
    client = Client()
    client.force_login(user=user)

    response = client.get("/va_data_management/")
    assert response.status_code == 403


# Show a VA and make sure the data is as expected
def test_show(user: User):
    can_view_record = Permission.objects.filter(codename="view_verbalautopsy").first()
    can_view_record_group = GroupFactory.create(permissions=[can_view_record])
    user = UserFactory.create(groups=[can_view_record_group])

    client = Client()
    client.force_login(user=user)
    va = VerbalAutopsyFactory.create()
    response = client.get(f"/va_data_management/show/{va.id}")
    assert response.status_code == 200
    assert bytes(va.Id10007, "utf-8") in response.content


# Request the show page for VA without permissions and make sure it's forbidden
def test_show_without_valid_permissions(user: User):
    client = Client()
    client.force_login(user=user)
    va = VerbalAutopsyFactory.create()
    response = client.get(f"/va_data_management/show/{va.id}")
    assert response.status_code == 403


# Request the edit form of a VA and make sure the data is as expected
def test_edit_with_valid_permissions(user: User):
    can_edit_record = Permission.objects.filter(codename="change_verbalautopsy").first()
    can_edit_record_group = GroupFactory.create(permissions=[can_edit_record])
    user = UserFactory.create(groups=[can_edit_record_group])

    client = Client()
    client.force_login(user=user)

    va = VerbalAutopsyFactory.create()
    response = client.get(f"/va_data_management/edit/{va.id}")
    assert response.status_code == 200
    assert bytes(va.Id10007, "utf-8") in response.content


# Request the edit form of a VA without permissions and make sure its forbidden
def test_edit_without_valid_permissions(user: User):
    client = Client()
    client.force_login(user=user)

    va = VerbalAutopsyFactory.create()
    response = client.get(f"/va_data_management/edit/{va.id}")
    assert response.status_code == 403


# Update a VA and make sure 1) the data is changed and 2) the history is tracked
def test_save_with_valid_permissions(user: User):
    can_edit_record = Permission.objects.filter(codename="change_verbalautopsy").first()
    can_view_record = Permission.objects.filter(codename="view_verbalautopsy").first()
    can_edit_view_record_group = GroupFactory.create(permissions=[can_edit_record, can_view_record])
    user = UserFactory.create(groups=[can_edit_view_record_group])

    client = Client()
    client.force_login(user=user)
    va = VerbalAutopsyFactory.create()
    assert va.history.count() == 1
    new_name = "Updated Example Name"
    response = client.post(f"/va_data_management/edit/{va.id}", { "Id10007": new_name })
    assert response.status_code == 302
    assert response["Location"] == f"/va_data_management/show/{va.id}"
    va = VerbalAutopsy.objects.get(id=va.id)
    assert va.Id10007 == new_name
    assert va.history.count() == 2
    assert va.history.first().history_user == user
    response = client.get(f"/va_data_management/show/{va.id}")
    # TODO: We need to handle timezones correctly
    assert bytes(va.history.first().history_date.strftime('%Y-%m-%d %H:%M'), "utf-8") in response.content
    assert bytes(va.history.first().history_user.name, "utf-8") in response.content


# Verify save access is restricted
def test_save_without_valid_permissions(user: User):
    client = Client()
    client.force_login(user=user)
    va = VerbalAutopsyFactory.create()
    assert va.history.count() == 1
    new_name = "Updated Example Name"
    response = client.post(f"/va_data_management/edit/{va.id}", { "Id10007": new_name })
    assert response.status_code == 403


# Reset an updated VA and make sure 1) the data is reset to original values and 2) the history is tracked
def test_reset_with_valid_permissions(user: User):
    can_edit_record = Permission.objects.filter(codename="change_verbalautopsy").first()
    can_edit_record_group = GroupFactory.create(permissions=[can_edit_record])
    user = UserFactory.create(groups=[can_edit_record_group])

    client = Client()
    client.force_login(user=user)
    va = VerbalAutopsyFactory.create()
    original_name = va.Id10007
    new_name = "Updated Name"
    client.post(f"/va_data_management/edit/{va.id}", { "Id10007": new_name })
    va = VerbalAutopsy.objects.get(id=va.id)
    assert va.Id10007 == new_name
    assert va.history.count() == 2
    # TODO: Switch the buttons to forms in show.html and make this a POST.
    response = client.get(f"/va_data_management/reset/{va.id}")
    assert response.status_code == 302
    assert response["Location"] == f"/va_data_management/show/{va.id}"
    va = VerbalAutopsy.objects.get(id=va.id)
    assert va.Id10007 == original_name
    assert va.history.count() == 3
    assert va.history.first().history_user == user


# Verify reset access is restricted
def test_reset_without_valid_permissions(user: User):
    client = Client()
    client.force_login(user=user)
    va = VerbalAutopsyFactory.create()
    response = client.get(f"/va_data_management/reset/{va.id}")
    assert response.status_code == 403


# Revert an updated VA and make sure 1) the data is reset to previous version and 2) the history is tracked
def test_revert_latest_with_valid_permissions(user: User):
    can_edit_record = Permission.objects.filter(codename="change_verbalautopsy").first()
    can_edit_record_group = GroupFactory.create(permissions=[can_edit_record])
    user = UserFactory.create(groups=[can_edit_record_group])

    client = Client()
    client.force_login(user=user)
    va = VerbalAutopsyFactory.create()
    original_name = va.Id10007
    second_name = "Second Name"
    third_name = "Third Name"
    client.post(f"/va_data_management/edit/{va.id}", { "Id10007": second_name })
    va = VerbalAutopsy.objects.get(id=va.id)
    assert va.Id10007 == second_name
    assert va.history.count() == 2
    client.post(f"/va_data_management/edit/{va.id}", { "Id10007": third_name })
    va = VerbalAutopsy.objects.get(id=va.id)
    assert va.Id10007 == third_name
    assert va.history.count() == 3
    # TODO: Switch the buttons to forms in show.html and make this a POST.
    response = client.get(f"/va_data_management/revert_latest/{va.id}")
    assert response.status_code == 302
    assert response["Location"] == f"/va_data_management/show/{va.id}"
    va = VerbalAutopsy.objects.get(id=va.id)
    assert va.Id10007 == second_name
    assert va.history.count() == 4
    assert va.history.first().history_user == user


# Verify revert access is restricted
def test_revert_latest_without_valid_permissions(user: User):
    client = Client()
    client.force_login(user=user)
    va = VerbalAutopsyFactory.create()
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
    district1 = province.add_child(name='District1', location_type='district')
    district2 = province.add_child(name='District2', location_type='district')
    facility = district1.add_child(name='Facility', location_type='facility')
    va = VerbalAutopsyFactory.create(location=facility)
    user.location_restrictions.set([district2]) # Should not have access to VA
    client = Client()
    client.force_login(user=user)
    response = client.get("/va_data_management/")
    assert response.status_code == 200
    assert bytes(va.Id10007, "utf-8") not in response.content
    response = client.get(f"/va_data_management/show/{va.id}")
    assert response.status_code == 404
    response = client.get(f"/va_data_management/edit/{va.id}")
    assert response.status_code == 404
    response = client.post(f"/va_data_management/edit/{va.id}", { "Id10007": "New Name" })
    assert response.status_code == 404
    response = client.get(f"/va_data_management/reset/{va.id}")
    assert response.status_code == 404
    response = client.get(f"/va_data_management/revert_latest/{va.id}")
    assert response.status_code == 404
