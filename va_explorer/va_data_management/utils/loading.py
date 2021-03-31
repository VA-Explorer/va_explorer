import pandas
from simple_history.utils import bulk_create_with_history
from datetime import datetime

from va_explorer.va_data_management.models import Location
from va_explorer.va_data_management.models import VerbalAutopsy
from va_explorer.va_data_management.models import CauseCodingIssue
from va_explorer.va_data_management.utils.validate import validate_vas_for_dashboard
from django.contrib.auth.models import User


def load_records_from_dataframe(record_df):
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
    for row in record_df.to_dict(orient='records'):
        if row['instanceid']:
            existing_va = VerbalAutopsy.objects.filter(instanceid=row['instanceid']).first()
            if existing_va:
                ignored_vas.append(existing_va)
                continue

        # If we got here, we need to create a new VA.
        # TODO: For now treat location as synthetic data and randomly assign a facility as the location
        va = VerbalAutopsy(**row)
        va.location = Location.objects.filter(location_type='facility').order_by('?').first()
        created_vas.append(va)

        try:
            # create a date object, assuming the csv date is formatted mm/dd/yyyy
            date_object = datetime.strptime(va.Id10023, '%m/%d/%Y').date()
            va.Id10023 = date_object
        except:
            va.Id10023 = "dk" # TODO instead of replacing this, could we keep the date as is and capture the issue?

        # the va.location is used to plot the record on the map
        # check if the location of death is a known facility
        location = va.Id10058
        known_facility = Location.objects.filter(location_type='facility', name=location).first()
        if known_facility is not None:
            va.location = known_facility
        else:
            # TODO create an "Unknown" location, this field has a not null requirement so we'll use a random default for now 
            va.location = Location.objects.filter(location_type='facility').order_by('?').first()

    new_vas = bulk_create_with_history(verbal_autopsies, VerbalAutopsy)
    
    # Add any errors to the db
    validate_vas_for_dashboard(new_vas)

    return {
        'ignored': ignored_vas,
        'created': created_vas,
    }

