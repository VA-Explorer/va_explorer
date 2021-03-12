import re

import pandas
from simple_history.utils import bulk_create_with_history

from va_explorer.va_data_management.models import Location
from va_explorer.va_data_management.models import VerbalAutopsy


def load_records_from_dataframe(record_df):
    # CSV can prefix column names with a dash or more, remove everything up to and including last dash
    record_df = record_df.rename(columns=lambda c: re.sub('^-*', '', c))

    # Figure out the common field names across the CSV and our model
    model_field_names = pandas.Index([f.name for f in VerbalAutopsy._meta.get_fields()])

    # But first, account for case differences in csv columns (i.e. ensure id10041 maps to Id10041)
    fieldCaseMapper = {field.lower(): field for field in model_field_names} 
    record_df.rename(columns=lambda c: fieldCaseMapper.get(c.lower(), c), inplace=True)

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

    # Populate the database!
    verbal_autopsies = [VerbalAutopsy(**row) for row in record_df.to_dict(orient='records')]
    # TODO: For now treat this as synthetic data and randomly assign a facility as the location
    for va in verbal_autopsies:
        va.location = Location.objects.filter(location_type='facility').order_by('?').first()
    bulk_create_with_history(verbal_autopsies, VerbalAutopsy)

    return {
        'verbal_autopsies': verbal_autopsies,
    }
