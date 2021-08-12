import pandas as pd
from pandas import to_datetime as to_dt
import numpy as np
from simple_history.utils import bulk_create_with_history
import logging
from django.contrib.auth import get_user_model
from django.db.models import Q

from va_explorer.va_data_management.models import VerbalAutopsy, VaUsername
from va_explorer.va_data_management.utils.validate import parse_date, validate_vas_for_dashboard
from va_explorer.va_data_management.utils.location_assignment import build_location_mapper, assign_va_location
from va_explorer.users.utils.demo_users import make_field_workers_for_facilities
from va_explorer.users.utils.field_worker_linking import assign_va_usernames, normalize_name


User = get_user_model()
import time


def load_records_from_dataframe(record_df, random_locations=False, debug=True):
    ti = t0 = time.time()
    logger = None if not debug else logging.getLogger("event_logger")
    if logger:
        logger.info("="*10 + "DATA INGEST" + "="*10)

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

    print('deduplicating fields...')
    # collapse fields ending with _other with their normal counterparts (e.x. Id10010_other, Id10010)
    record_df = deduplicate_columns(record_df)
    
    # if field worker column available (Id10010), standardize names
    if "Id10010" in record_df.columns:
        record_df["Id10010"] = record_df["Id10010"].apply(normalize_name).replace(np.nan, "UNKNOWN")

    tf = time.time(); print(f"time: {tf - ti} secs"); ti = tf
            
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
    location_map = {}
    
    # build location mapper to map csv locations to known db locations
    if "hospital" in record_df.columns:
        location_map = build_location_mapper(record_df["hospital"].unique().tolist())
        
    # if random locations, assign random locations via a random field worker.
    if random_locations:
        valid_usernames = VaUsername.objects.exclude(va_username__exact='')
        # if no field workers with usernames, create some
        if len(valid_usernames) <= 1:
            print('WARNING: no field workers w/ usernames in system. Generating random ones now...')
            make_field_workers_for_facilities()
            valid_usernames = VaUsername.objects.exclude(va_username__exact='')

    # pull in all existing VA instanceIDs from db for deduping purposes
    print('pulling in instance ids...')
    va_instance_ids = set(VerbalAutopsy.objects.values_list('instanceid', flat=True))
    tf = time.time(); print(f"time: {tf - ti} secs"); ti = tf

    if debug:
        print(f"# of VAs: {record_df.shape[0]}, # of instanceIDs: {record_df.instanceid.nunique()}")

    print("creating new VAs...")
    for i, row in enumerate(record_df.to_dict(orient='records')):
        va = VerbalAutopsy(**row)
        # only import VA if its instanceId doesn't already exist
        if row['instanceid']:
            #existing_va = VerbalAutopsy.objects.filter(instanceid=row['instanceid']).first()
            va_exists = (row['instanceid'] in va_instance_ids)
            if va_exists:
                ignored_vas.append(va)
                continue
            else:
                va_instance_ids.add(row['instanceid'])
            
        
        # If we got here, we have a new, legit VA on our hands.
        va_id = row.get('instanceid', f"{i} of {record_df.shape[0]}")
        
        
        # Try to parse date of death as as datetime. Otherwise, record string and add record issue during validation
        parsed_date = parse_date(va.Id10023, strict=False)
        if logger:
            logger.info(f"va_id: {va_id} - Parsed {parsed_date} for Date of Death from {va.Id10023}") 
        va.Id10023 = parsed_date

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
            if "hospital" in row and logger:
                logger.info(f"va_id: {va_id} - Matched hospital {row['hospital']} to {va.location} location in DB")
            
        created_vas.append(va)

    tf = time.time(); print(f"time: {tf - ti} secs"); ti = tf

    print('populating DB...')
    new_vas = bulk_create_with_history(created_vas, VerbalAutopsy)

    tf = time.time(); print(f"time: {tf - ti} secs"); ti = tf

    # link VAs to known field workers in the system
    print("assigning VA usernames to known field workers...")
    assign_va_usernames(new_vas)
    tf = time.time(); print(f"time: {tf - ti} secs"); ti = tf
    
    print("Validating VAs...")
    # Add any errors to the db
    validate_vas_for_dashboard(new_vas)
    tf = time.time(); print(f"time: {tf - ti} secs"); ti = tf

    print(f"total time: {time.time() - t0}")

    return {
        'ignored': ignored_vas,
        'created': created_vas,
    }
  
# combine fields ending with _other with their normal counterparts (e.x. Id10010_other, Id10010). 
# in Zambia data, often either the normal or _other field has a value but not both.
# NOTE: currently using 'cleaned' version of other field (called filtered_<field>_other) and discarding <field>-other values
# verify that this is kosher. 
def deduplicate_columns(record_df, drop_duplicates=True):
    other_cols = record_df.filter(regex='\_other$', axis=1).columns
    # get original columns that other columns are derived from
    original_cols = list(set(other_cols.str.replace('^filtered\_', '').str.replace('_other$', '').tolist()))
    for original_col in original_cols:

        # If original column exists, combine values from original and _other columns into a single column
        if original_col in record_df.columns:
            record_df[original_col] = (record_df
                                        .filter(regex=original_col, axis=1)
                                        .replace('other', np.nan)
                                        .bfill(axis=1).iloc[:,0])
            #record_df[original_col] = record_df.apply(lambda row: row[other_col] if pd.isnull(row[original_col]) else row[original_col], axis=1)
        else:
            print(f"WARNING: couldn't find {original_col} but {original_col}_other in columns")
    if drop_duplicates:
        record_df = record_df.drop(columns=other_cols)
    return record_df

def get_va_summary_stats(vas):
    # track last data update and submission date
    stats = {'last_submission': None, 'last_update': None, 'total_vas': vas.count()}
    if stats['total_vas'] > 0:
        # Track last time VAs were updated. Again, using last import date so may need to change.
        last_update = max(vas.values_list('created', flat=True))
        if not pd.isnull(last_update):
            stats['last_update'] =  last_update.strftime('%d %b, %Y')
        # Record latest submission date (from ODK). Column may/may not be available depending on source
        raw_submissions =  vas.values_list('submissiondate', flat=True)

        # track number of ineligible VAs for dashboard
        stats['ineligible_vas'] = vas.filter(Q(Id10023__in=['DK','dk']) | Q(Id10023__isnull=True)|\
         Q(location__isnull=True)).count()
        if raw_submissions.count() > 0:
            try:
                last_submission = to_dt(raw_submissions).max()
            except:
                last_submission = to_dt(pd.Series(to_dt(raw_submissions, utc=True)).dt.date).max()
            if not pd.isnull(last_submission):
                stats['last_submission'] = last_submission.strftime('%d %b, %Y')
    return stats


