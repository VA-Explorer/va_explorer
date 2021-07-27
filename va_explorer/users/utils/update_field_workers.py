from va_explorer.va_data_management.models import VerbalAutopsy, Location
from va_explorer.va_data_management.utils.location_assignment import build_location_mapper
from va_explorer.users.models import User
import pandas as pd


def update_loc_restrictions(filename="pilot_location_restrictions.csv"):
	loc_df = pd.read_csv(filename)
	print(f"{loc_df.shape[0]} Users to update")
	update_ct = 0
	db_locations = list(Location.objects.all().values_list('name', flat=True))
	loc_mapper = build_location_mapper(loc_df['location_restrictions'].tolist(), db_locations)
	for i, row in loc_df.iterrows():
		user_email = row["email"]
		user_obj = User.objects.filter(email=user_email).first()
		if user_obj:
			location_name = loc_mapper.get(row['location_restrictions'], None)
			db_location = Location.objects.filter(name=location_name).first()
			if db_location:
				user_obj.location_restrictions.set([db_location.pk])
				print(f"updated user {user_obj.name}'s location to {location_name}")
				user_obj.save()
				update_ct +=1
	print(f"updated {update_ct} Users in system")