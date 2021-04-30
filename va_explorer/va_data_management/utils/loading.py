import pandas as pd
from simple_history.utils import bulk_create_with_history
from datetime import datetime
import re

from va_explorer.va_data_management.models import Location
from va_explorer.va_data_management.models import VerbalAutopsy
from va_explorer.va_data_management.models import VaUsername
from va_explorer.va_data_management.models import CauseCodingIssue
from fuzzywuzzy import fuzz


from va_explorer.va_data_management.utils.validate import parse_date, validate_vas_for_dashboard

from django.contrib.auth import get_user_model

from va_explorer.users.utils import make_field_workers_for_facilities

User = get_user_model()

def load_records_from_dataframe(record_df, random_locations=False):
    # CSV can prefix column names with a strings and a dash or more. Examples:
    #     presets-Id10004
    #     respondent-backgr-Id10008
    #     -Id10008
    # Remove everything up to and including last dash.
    record_df = record_df.rename(columns=lambda c: c.rsplit('-', 1)[-1])

    # Figure out the common field names across the CSV and our model
    model_field_names = pd.Index([f.name for f in VerbalAutopsy._meta.get_fields()])

    # But first, account for case differences in csv columns (i.e. ensure id10041 maps to Id10041)
    fieldCaseMapper = {field.lower(): field for field in model_field_names} 
    record_df.rename(columns=lambda c: fieldCaseMapper.get(c.lower(), c), inplace=True)

    # Lowercase the instanceID column that can come from ODK as "instanceID".
    if 'intanceID' in record_df.columns:
        record_df = record_df.rename(columns={'instanceID': 'instanceid'})

    # If there is not an instanceid column but there is a key column,
    # populate instanceid field with key value.
    if 'instanceid' not in record_df.columns and 'key' in record_df.columns:
        record_df = record_df.rename(columns={'key': 'instanceid'})
            
    csv_field_names = record_df.columns
    common_field_names = csv_field_names.intersection(model_field_names)

    # Just keep the fields in the CSV that we have columns for in our VerbalAutopsy model
    # Also track extras or missing fields for eventual debugging display
    missing_field_names = model_field_names.difference(common_field_names)
    extra_field_names = csv_field_names.difference(common_field_names)
    record_df = record_df[common_field_names]

    # For each row, check to see if there is an instanceid.
    # If there is instanceid, try to find existing VA with that instanceid.
    # If row does not have an instanceid, it will create a new VA.
    # Build a list of VAs to create and a list of VAs to ignore (that already exist).
    ignored_vas = []
    created_vas = []
    date_issue_ids = []
    location_map = {}
    
    # build location mapper to map csv locations to known db locations
    if "hospital" in record_df.columns:
        location_map = build_location_mapper(record_df["hospital"])
        
    # if random locations, assign random locations via a random field worker.
    if random_locations:
        valid_usernames = VaUsername.objects.exclude(va_username__exact='')
        # if no field workers with usernames, create some
        if len(valid_usernames) <= 1:
            print('WARNING: no field workers w/ usernames in system. Generating random ones now...')
            make_field_workers_for_facilities()
            valid_usernames = VaUsername.objects.exclude(va_username__exact='')
            
    # build location matching index for location assignment
    for i, row in enumerate(record_df.to_dict(orient='records')):
        if row['instanceid']:
            existing_va = VerbalAutopsy.objects.filter(instanceid=row['instanceid']).first()
            if existing_va:
                ignored_vas.append(existing_va)
                continue

        # If we got here, we need to create a new VA.
        va = VerbalAutopsy(**row)
        

        # Try to parse date of death as as datetime. Otherwise, record string and add record issue during validation
        va.Id10023 = parse_date(va.Id10023, strict=False)

        # Try mapping va location to known db location. If not possible, set to null location
        
        # if random_locations, assign random field worker to VA which can be used to determine location.
        # Otherwise, try assigning location based on hospital field. 
        if random_locations:
            username = valid_usernames.order_by('?').first()
            user = User.objects.get(pk=username.user_id)
            va.username = username.va_username
            va.location = user.location_restrictions.first()
        else:
            assign_va_location(va, location_map)
            
        created_vas.append(va)


    new_vas = bulk_create_with_history(created_vas, VerbalAutopsy)
    
    # Add any errors to the db
    validate_vas_for_dashboard(new_vas)

    return {
        'ignored': ignored_vas,
        'created': created_vas,
    }
  
def build_location_mapper(va_locations, db_locations=None, loc_type="facility", drop_terms=None, similarity_thresh=75):
   
    # store database locations of type location_type in a df 
    if not db_locations:
        db_locations = list(Location.objects.filter(location_type=loc_type).values_list('name', flat=True))
    location_df = pd.DataFrame({'name': db_locations}).assign(key = lambda df: df['name'].str.lower())
    
    # store unique va_locations in mapper dataframe
    va_locations = list(set(va_locations).difference(set(['other'])))
    mapper = pd.DataFrame({"va_name": va_locations})
    mapper['va_key'] = mapper['va_name'].str.lower().replace("\_", " ", regex=True)

    # preprocess dataframes
    if not drop_terms:
        drop_terms = ['general', 'central', 'teaching']
        
    for term in drop_terms:
        location_df['key'] = location_df['key'].replace(f" {term}", "", regex=True)
        mapper['va_key'] = mapper['va_key'].replace(f" {term}", "", regex=True)
    
    # matching
    mapper["db_name"] = mapper["va_key"].apply(lambda x: fuzzy_match(x, option_df=location_df, threshold=similarity_thresh))
    
    return mapper.set_index("va_name")["db_name"].to_dict()
    
    
def assign_va_location(va, location_mapper, location_fields=None):
    # check if the hospital or place of death fields are known locations
    location_fields = ['hospital', 'hospital_other'] if not location_fields else location_fields
    
    db_location = None
    for location_field in location_fields:
        location = va.__dict__.get(location_field, None)
        if location:
            db_location_name = location_mapper.get(location, None)
            if db_location_name:
                # TODO: make this more generic to other location hierarchies
                db_location = Location.objects.filter(location_type='facility', name=db_location_name).first()
                break
        
    if db_location:
        va.location = db_location
    # otherwise, set location to 'Unknown' (null)
    else:
        va.set_null_location()
    return va
        
        
def fuzzy_match(search, options=None, option_df=pd.DataFrame(), threshold=75, preprocess=False, drop_terms=None, prnt=False):
    match = None
    if not pd.isnull(search):
        if not options and option_df.size == 0:
            raise ValueError("Please provide an option list or option_df (dataframe with options in 'name' column)")
        # if options not in dataframe format, create one to store them
        if option_df.size == 0:
            option_df = (pd.DataFrame({'name': options}).assign(key = lambda df: df['name'].str.lower()))
    
        # if preprocess=True, clean search term and options before comparing
        search_term = search
        if preprocess:
            if not drop_terms:
                drop_terms = ['general', 'central', 'teaching']
                
            search_term = re.sub('\_', ' ', search.lower())    
            for term in drop_terms:
                search_term = search_term.replace(f" {term}", "")
                option_df['key'] = option_df['key'].replace(f" {term}", "", regex=True)
        
        # matching
        option_df['score'] = option_df['key'].apply(lambda x: fuzz.ratio(search_term, x))
        option_df = option_df.sort_values(by='score', ascending=False)
        
        if prnt: print(option_df.head())
        
        # filter to only matches exceeding threshold
        option_df = option_df.query("score >= @threshold")
        
        if prnt: print(option_df)
        
        if option_df.size > 0:     
            match = option_df.iloc[0]['name']
    
    return match
        

