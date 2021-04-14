import pandas
from simple_history.utils import bulk_create_with_history
from datetime import datetime

from va_explorer.va_data_management.models import Location
from va_explorer.va_data_management.models import VerbalAutopsy
from va_explorer.va_data_management.models import VaUsername
from va_explorer.va_data_management.models import CauseCodingIssue

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
    model_field_names = pandas.Index([f.name for f in VerbalAutopsy._meta.get_fields()])

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
    
    # if random locations, assign random locations via a random field worker.
    if random_locations:
        valid_usernames = VaUsername.objects.exclude(va_username__exact='')
        # if no field workers with usernames, create some
        if len(valid_usernames) <= 1:
            print('WARNING: no field workers w/ usernames in system. Generating random ones now...')
            make_field_workers_for_facilities()
            valid_usernames = VaUsername.objects.exclude(va_username__exact='')            

    for i, row in enumerate(record_df.to_dict(orient='records')):
        if row['instanceid']:
            existing_va = VerbalAutopsy.objects.filter(instanceid=row['instanceid']).first()
            if existing_va:
                ignored_vas.append(existing_va)
                continue

        # If we got here, we need to create a new VA.
        va = VerbalAutopsy(**row)
        va.location = Location.objects.filter(location_type='facility').order_by('?').first()
        created_vas.append(va)


        # Try to parse date of death as as datetime. Otherwise, add to date issues if row has instance id
        va.Id10023 = parse_date(va.Id10023, strict=False)


        # if random_locations, assign random field worker to VA which can be used to determine location
        if random_locations:
            username = valid_usernames.order_by('?').first()
            user = User.objects.get(pk=username.user_id)
            va.username = username.va_username
            va.location = user.location_restrictions.first()
        else:
            # check if the place of of death is a known facility
            location = va.Id10058
            known_facility = Location.objects.filter(location_type='facility', name=location).first()
            if known_facility is not None:
                va.location = known_facility
            # otherwise, set location to 'Unknown' (null)
            else:
                va.set_null_location()

    new_vas = bulk_create_with_history(created_vas, VerbalAutopsy)
    
    # Add any errors to the db
    validate_vas_for_dashboard(new_vas)

#=======
#    bulk_create_with_history(created_vas, VerbalAutopsy)
#    
#    # if any date issues, try to report them now that VAs are tagged
#    for issue_id in date_issue_ids:
#        # only create an issue if we can find VA via instanceid
#        bad_va = VerbalAutopsy.objects.filter(instanceid=issue_id).first()
#        if bad_va:
#            issue_text = f"Error: field Id10023, couldn't parse date from {bad_va.Id10023}"
#            issue = CauseCodingIssue(verbalautopsy_id=bad_va.id, text=issue_text, severity='error', algorithm='', settings='')
#            issue.save()
#
#        
#>>>>>>> added more rubust date parsing and got all tests to work

    return {
        'ignored': ignored_vas,
        'created': created_vas,
    }

