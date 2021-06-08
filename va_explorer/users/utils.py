#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Apr 12 14:33:57 2021

@author: babraham
"""

from django.contrib.auth.models import Group
from django.db.models import F
from django.contrib.auth.models import Permission
from django.utils.crypto import get_random_string


from va_explorer.users.models import User
from va_explorer.va_data_management.models import Location

import pandas as pd
import re



def get_app_permissions(app_names=None):
    perms = Permission.objects.values_list('content_type__app_label', 'codename')
    perm_df = pd.DataFrame.from_records(perms, columns=['app', 'codename'])
    if app_names:
        perm_df = perm_df.query("app==@app_names")
        if perm_df.shape == 0:
            print(f"WARNING: couldnt find permissions for app(s) {app_names}")
    return perm_df


# bulk create a list of users from a csv file. Can specify name, email, group (user role), location restrictions, and permissions
def create_users_from_csv(user_list_file):
    user_df = pd.read_csv(user_list_file)
    # initialize counters and dictionaries
    new_user_ct = 0
    # dictionaries for group and location matching
    group_dict = {g.name.lower(): g for g in Group.objects.all()}
    location_dict = {l.name.lower(): l for l in Location.objects.all()}
    
    for i, user_data in user_df.iterrows():
        # check if email already exists
        name, email = user_data['name'], user_data['email']
        if not re.match('[^@]+@[^@]+\.[^@]+', email):
            print(f'Invalid email address found: {email}')
            continue
        if len(name.strip()) == 0:
            name = email
        if User.objects.filter(email=email).exists():
            print(f'User account already exists for email {email}')
        else:
            user, created = User.objects.get_or_create(email=email, defaults={'name': name, 'is_active': True})
            if created:
                
                password = get_random_string(length=8)
                user.set_password(password)
                # Need to save after setting password.
                user.save()
                
                # determine and set user group if provided
                group = user_data.get("group", None)
                if not pd.isnull(group):
                    group = group.lower()
                    group += "s" if not group.endswith('s') else group
                    known_group = group_dict.get(group, None)
                    if known_group:
                        user.groups.add(*[known_group])
                    else:
                        print(f"WARNING: couldnt match {user_data['group']} to known groups")
                       
                # determine and set location restirctions if provided. For now, assumes one location provided
                restriction = user_data.get("location_restrictions", None)
                if not pd.isnull(restriction):
                    # try to match location to known db locations
                    known_location = location_dict.get(restriction.lower(), None)
                    if  known_location:
                        user.location_restrictions.add(*[known_location])
                    else:
                        print(f"WARNING: couldnt match {user_data['location_restrictions']} to known locations")
                        
                # TODO: parse user permission
                
                # save again to update user fields
                user.save()
                print(f'Created account for user {name} with email {email} and temporary password {password}')
                new_user_ct +=1
                
    print(f"Created {new_user_ct} new users")

# get table with basic info for all users in system. No PII included in result
def get_anonymized_user_info():      
    user_data = User.objects\
    .select_related('location_restrictions')\
    .select_related('groups')\
    .values(
            'uuid',
            'is_active',
            'is_staff',
            role = F('groups__name'),
            locations = F('location_restrictions__name')           
    )
    
    return pd.DataFrame.from_records(user_data).rename(columns={'locations': 'location_restrictions'})

def make_field_workers_for_facilities(facilities=None, num_per_facility=2):
    if not facilities:
        facilities = Location.objects.filter(location_type='facility').exclude(name='Unknown')
    
    for i, facility in enumerate(facilities):
        for j in range(num_per_facility):
            worker_id = (i * num_per_facility) + j + 1
            create_demo_field_worker(worker_id, facility)
        

def create_demo_field_worker(worker_id, facility=None):

    username = f"field_worker_{worker_id}"

    user, created = User.objects.get_or_create(
        email=f"{username}@example.com",
        defaults={"name": f"Demo Field Worker {worker_id}", "is_active": True, "has_valid_password": True},
    )

    if created:
        # assign password and save user
        user.set_password("Password1")
        user.save()
        
        # set their username
        user.set_va_username(*[username])
        
        # assign new user to field worker group
        user_group = Group.objects.get(name="Field Workers")
        user_group.user_set.add(user)
        # save user group changes
        user_group.save()
        
        # if facility name provided, assign field worker. Otherwise, randomly assign one
        if not facility:
            facility = Location.objects.filter(location_type='facility').order_by('?').first()
        
        user.location_restrictions.add(*[facility])
        
        # save/export final user
        user.save()
        
        print(f"Successfully created field worker with username {username} for facility {facility.name}")
        