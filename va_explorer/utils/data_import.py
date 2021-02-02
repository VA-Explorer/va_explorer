#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Nov 16 16:57:22 2020

@author: babraham
"""

from va_explorer.va_data_management.models import VerbalAutopsy, Location
from simple_history.utils import bulk_create_with_history
import pandas as pd
import re


def load_records_from_dataframe(record_df):
    
    # CSV can prefix column names with a dash or more, remove everything up to and including last dash
    record_df.rename(columns=lambda c: re.sub('^.*-', '', c), inplace=True)

    # Figure out the common field names across the CSV and our model
    model_field_names = pd.Index([f.name for f in VerbalAutopsy._meta.get_fields()])
    
    # But first, account for case differences in csv columns (i.e. ensure id10041 maps to Id10041)
    fieldCaseMapper = {field.lower(): field for field in model_field_names} 
    record_df.rename(columns=lambda c: fieldCaseMapper.get(c.lower(), c), inplace=True)

    # if no instanceid column but key column exists, populate instanceid field with key values
    if 'instanceid' not in record_df.columns:
        if 'key' in record_df.columns:
            record_df = record_df.rename(columns={'key':'instanceid'})


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

    print(f'Loaded {len(verbal_autopsies)} verbal autopsies')
