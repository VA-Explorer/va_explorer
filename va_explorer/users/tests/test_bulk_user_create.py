import pytest
import pandas as pd
from va_explorer.users.models import User
from va_explorer.users.utils.user_form_backend import fill_user_form_data, create_users_from_file
from va_explorer.users.validators import validate_user_form, validate_user_object
from va_explorer.users.tests.user_test_utils import setup_test_db, get_fake_user_data

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
	