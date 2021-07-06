import pytest
import pandas as pd
import re

from django.contrib.auth.models import Group
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from va_explorer.tests.factories import UserFactory, LocationFactory, VerbalAutopsyFactory
from va_explorer.va_data_management.models import Location
from va_explorer.users.models import User, UserPasswordHistory
from va_explorer.users.utils.user_form_backend import fill_user_form_data, create_users_from_file
from va_explorer.users.validators import validate_user_form, validate_user_object
from va_explorer.users.management.commands.initialize_groups import GROUPS_PERMISSIONS

pytestmark = pytest.mark.django_db


def test_fill_user_form_data(): 
	setup_test_db()
	users = get_fake_user_data()

	for user, user_data in users.items():
		user_form = fill_user_form_data(user_data)
		validate_user_form(user_data, user_form)
		# save user and assert it was created correctly
		user_form.save(email_confirmation=False)
		user_obj = User.objects.filter(email=user_data["email"]).first()
		assert user_obj

def test_create_users_from_file():
	setup_test_db()
	# read in user file
	user_file = "va_explorer/users/tests/test_users.csv"
	user_df = pd.read_csv(user_file).replace({"TRUE": True, "FALSE": False})
	for permission in ["view_pii", "download_data"]:
		if permission in user_df.columns:
			user_df[permission] = user_df[permission].fillna(False)
	# fill all other NAs with empty strings
	user_df = user_df.fillna("")

	res = create_users_from_file(user_file)

	assert res["user_ct"] == user_df.shape[0] and res["error_ct"] == 0
	assert len(res["users"]) == user_df.shape[0]

	user_emails = set([u.email for u in res['users']])
	raw_emails = set(user_df["email"].tolist())

	assert len(user_emails) == len(raw_emails) == len(user_emails.intersection(raw_emails))

	for i, user_data in user_df.iterrows():
		user_object = list(filter(lambda x: x.email==user_data["email"], res["users"]))[0]
		validate_user_object(user_data, user_object)

def setup_test_db():
	province = LocationFactory.create(name="Province1")
	districtX = province.add_child(name='DistrictX', location_type='district')
	facility1 = districtX.add_child(name='Facility1', location_type='facility')
	districtY = province.add_child(name='DistrictY', location_type='district')
	facility2 = districtY.add_child(name='Facility2', location_type='facility')
	facility3 = districtY.add_child(name='Facility3', location_type='facility')

	# Each facility with one VA
	va1 = VerbalAutopsyFactory.create(location=facility1)
	va2 = VerbalAutopsyFactory.create(location=facility2)
	va3 = VerbalAutopsyFactory.create(location=facility3)

	# create user groups defined in initialize_groups.py
	for group_name, group_permissions in GROUPS_PERMISSIONS.items():
		group, created = Group.objects.get_or_create(name=group_name)
		if group.permissions.exists():
			group.permissions.clear()
		for model_class, model_permissions in group_permissions.items():
			for codename in model_permissions:
				# Get the content type for the given model class.
				content_type = ContentType.objects.get_for_model(model_class)

				# Lookup permission based on content type and codename.
				try:
					permission = Permission.objects.get(content_type=content_type, codename=codename)
					group.permissions.add(permission)
				except:
					pass

# create three dummy users for testing, each with different roles, location restirctions, and privacy privileges
def get_fake_user_data():
	users = {}
	# user 1: restricted to location X, data viewer, cant view PII but can download data
	users["u1"] = {'name': 'user1', 'email': 'user1@example.com', 'location_restrictions': 'DistrictX',
	'group': 'Data Viewer', 'view_pii': False, 'download_data': True}

	# user 2: data manager restricted to districtY, can view PII and can download data
	users["u2"] = {'name': 'user2', 'email': 'user2@example.com', 'location_restrictions': 'DistrictY',
	'group': 'Data Manager', 'view_pii': True, 'download_data': True}

	# user 3: dashboard viewer - no location restrictions, cannot view PII but can download data
	users["u3"] = {'name': 'user3', 'email': 'user3@example.com',
	'group': 'Dashboard Viewer', 'view_pii': False, 'download_data': True}

	return users
	