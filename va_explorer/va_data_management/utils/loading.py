import logging
import time

import numpy as np
import pandas as pd
from django.contrib.auth import get_user_model
from django.db.models import Count, Max, Q
from simple_history.utils import bulk_create_with_history

from va_explorer.users.utils.demo_users import make_field_workers_for_facilities
from va_explorer.users.utils.field_worker_linking import (
    assign_va_usernames,
    normalize_name,
)
from va_explorer.va_data_management.models import Location, VaUsername, VerbalAutopsy
from va_explorer.va_data_management.utils.date_parsing import parse_date
from va_explorer.va_data_management.utils.location_assignment import (
    assign_va_location,
    build_location_mapper,
)
from va_explorer.va_data_management.utils.validate import validate_vas_for_dashboard

from ..constants import _checkbox_choices

User = get_user_model()


# load VA records into django database
def load_records_from_dataframe(record_df, random_locations=False, debug=True):
    ti = t0 = time.time()
    logger = None if not debug else logging.getLogger("event_logger")
    if logger:
        header = "=" * 10 + "DATA INGEST" + "=" * 10
        logger.info(header)

    # CSV can prefix column names with a strings and a dash or more. Examples:
    #     presets-Id10004
    #     respondent-backgr-Id10008
    #     -Id10008
    # Remove everything up to and including last dash.
    record_df = record_df.rename(columns=lambda c: c.rsplit("-", 1)[-1])

    # Figure out the common field names across the CSV and our model
    model_field_names = pd.Index([f.name for f in VerbalAutopsy._meta.get_fields()])

    # But first, account for case differences in csv columns (i.e. ensure id10041 maps to Id10041)
    field_case_mapper = {field.lower(): field for field in model_field_names}
    record_df.rename(
        columns=lambda c: field_case_mapper.get(c.lower(), c), inplace=True
    )

    # Lowercase the instanceID column that can come from ODK as "instanceID".
    if "instanceID" in record_df.columns:
        record_df = record_df.rename(columns={"instanceID": "instanceid"})

    # If there is not an instanceid column but there is a key column,
    # populate instanceid field with key value.
    if "instanceid" not in record_df.columns and "key" in record_df.columns:
        record_df = record_df.rename(columns={"key": "instanceid"})

    print("de-duplicating fields...")
    # collapse fields ending with _other with their normal counterparts (e.x. Id10010_other, Id10010)
    record_df = deduplicate_columns(record_df)

    # if field worker column available (Id10010), standardize names
    if "Id10010" in record_df.columns:
        record_df["Id10010"] = (
            record_df["Id10010"].apply(normalize_name).replace(np.nan, "UNKNOWN")
        )

    tf = time.time()
    print(f"time: {tf - ti} secs")
    ti = tf

    csv_field_names = record_df.columns
    common_field_names = csv_field_names.intersection(model_field_names)

    # Just keep the fields in the CSV that we have columns for in our VerbalAutopsy model
    if logger:
        missing_field_names = model_field_names.difference(common_field_names)
        logger.debug("Missing fields: %s", missing_field_names)
        extra_field_names = csv_field_names.difference(common_field_names)
        logger.debug("Extra fields: %s", extra_field_names)
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
        valid_usernames = VaUsername.objects.exclude(va_username__exact="")
        # if no field workers with usernames, create some
        if len(valid_usernames) <= 1:
            print(
                "WARNING: no field workers w/ usernames in system. Generating random ones now..."
            )
            make_field_workers_for_facilities()
            valid_usernames = VaUsername.objects.exclude(va_username__exact="")

    # pull in all existing VA instanceIDs from db for de-duping purposes
    print("pulling in instance ids...")
    va_instance_ids = set(VerbalAutopsy.objects.values_list("instanceid", flat=True))
    tf = time.time()
    print(f"time: {tf - ti} secs")
    ti = tf

    if debug:
        print(
            f"# of VAs: {record_df.shape[0]}, # of instanceIDs: {record_df.instanceid.nunique()}"
        )

    print("creating new VAs...")
    for i, row in enumerate(record_df.to_dict(orient="records")):
        format_multi_select_fields(row)

        va = VerbalAutopsy(**row)
        # only import VA if its instanceId doesn't already exist
        if row["instanceid"]:
            va_exists = row["instanceid"] in va_instance_ids
            if va_exists:
                ignored_vas.append(va)
                continue
            else:
                va_instance_ids.add(row["instanceid"])

        # If we got here, we have a new, legit VA on our hands.
        va_id = row.get("instanceid", f"{i} of {record_df.shape[0]}")

        # Try to parse date of death as as datetime. Otherwise, record string and
        # add record issue during validation
        parsed_date = parse_date(va.Id10023, strict=False)
        if logger:
            logger.info(
                f"va_id: {va_id} - Parsed {parsed_date} for Date of Death from {va.Id10023}"
            )
        va.Id10023 = parsed_date

        # Try to parse submission date as as datetime. Otherwise, record string and
        # add record issue during validation
        parsed_sub_date = parse_date(va.submissiondate, strict=False)
        if logger:
            logger.info(
                f"va_id: {va_id} - Parsed {parsed_sub_date} as Submission Date from {va.submissiondate}"
            )
        va.submissiondate = parsed_sub_date

        # if random_locations, assign random field worker to VA which can be used
        # to determine location.
        # Otherwise, try assigning location based on hospital field.
        if random_locations:
            username = valid_usernames.order_by("?").first()
            user = User.objects.get(pk=username.user_id)
            va.username = username.va_username
            va.location = user.location_restrictions.first()
        else:
            assign_va_location(va, location_map)
            if "hospital" in row and logger:
                logger.info(
                    f"va_id: {va_id} - Matched hospital \
                            {row['hospital']} to {va.location} location in DB"
                )

        # Generate a unique_identifier_hash for each VA if the application is configured to detect duplicate VAs
        if VerbalAutopsy.auto_detect_duplicates():
            va.generate_unique_identifier_hash()
        created_vas.append(va)

    tf = time.time()
    print(f"time: {tf - ti} secs")
    ti = tf

    print("populating DB...")
    new_vas = bulk_create_with_history(created_vas, VerbalAutopsy)

    tf = time.time()
    print(f"time: {tf - ti} secs")
    ti = tf

    # link VAs to known field workers in the system
    print("assigning VA usernames to known field workers...")
    assign_va_usernames(new_vas)
    tf = time.time()
    print(f"time: {tf - ti} secs")
    ti = tf

    print("Validating VAs...")
    # Add any errors to the db
    validate_vas_for_dashboard(new_vas)
    tf = time.time()
    print(f"time: {tf - ti} secs")
    ti = tf

    print(f"total time: {time.time() - t0}")

    # Mark duplicate VAs if the application is configured to do so
    if VerbalAutopsy.auto_detect_duplicates():
        print("Marking VAs as duplicate...")
        VerbalAutopsy.mark_duplicates()

    return {
        "ignored": ignored_vas,
        "created": created_vas,
    }


# Change the response format of Multiselect questions from ODK (space-separated)
# into the format that we expect for rendering in the UI (comma-separated)
def format_multi_select_fields(row):
    for multi_select_question in _checkbox_choices:
        if multi_select_question in row and isinstance(row[multi_select_question], str):
            # Convert to comma-separated
            row[multi_select_question] = ",".join(
                response for response in row[multi_select_question].split()
            )
            # If the selection is snake case, convert to title case per our implementation
            for response in row[multi_select_question]:
                response.replace("_", " ").title()


# load locations from a csv file into the django database. If delete_previous
# is true, will clear location db before laoding.
def load_locations_from_file(csv_file, delete_previous=False):
    # Delete existing locations ONLY IF DELETE_PREVIOUS IS TRUE.
    if delete_previous:
        # Clear out any existing locations (this is for initialization only)
        Location.objects.all().delete()

    # Load the CSV file
    csv_data = pd.read_csv(csv_file, keep_default_na=False).rename(
        columns=lambda c: c.lower()
    )

    # rename type column to match model field name
    if "type" in csv_data.columns:
        csv_data = csv_data.rename(columns={"type": "location_type"})

    # only consider fields in both csv and Location schema
    db_fields = set([field.name for field in Location._meta.get_fields()])
    common_fields = csv_data.columns.intersection(db_fields).tolist()

    # track number of new locations added to system
    location_ct = update_ct = 0
    db_locations = {location.name: location for location in Location.objects.all()}
    # Store it into the database in a tree structure
    # *** assumes locations have following fields: name, parent, location_type
    for _, row in csv_data.iterrows():
        model_data = row.loc[common_fields].dropna()
        if row["parent"]:
            # first, check that parent exists. If not, skip location due to integrity issues
            parent_node = db_locations.get(row["parent"], None)
            if parent_node:
                # update parent to get latest state
                parent_node.refresh_from_db()
                # next, check for current node in db. If not, create new child.
                # If so, ensure parent matches parent_node
                row_location = db_locations.get(row["name"], None)
                if row_location:
                    # if child node points to right parent
                    if row_location.get_parent().name != parent_node.name:
                        print(
                            f"WARNING: Updating {row_location.name}'s parent to {parent_node.name}"
                        )
                        row_location.move(parent_node, pos="sorted-child")
                    # update existing location fields with data from csv
                    for field, value in model_data.items():
                        if value not in [np.nan, "", None]:
                            setattr(row_location, field, value)
                    row_location.save()
                    update_ct += 1
                else:
                    print(f"Adding {row['name']} as child node of {row['parent']}")
                    db_locations[row["name"]] = parent_node.add_child(**model_data)
                    location_ct += 1
            else:
                print(
                    f"Couldn't find location {row['name']}'s parent ({row['parent']}) in system. Skipping.."
                )
        else:
            # add root node if it doesn't already exist
            if not db_locations.get(row["name"], None):
                print(f"Adding root node for {row['name']}")
                db_locations[row["name"]] = Location.add_root(**model_data)
                location_ct += 1

    # if non existent, add 'Null' location to database to account for VAs with unknown locations
    if not Location.objects.filter(name="Unknown").exists():
        print("Adding NULL location to handle unknowns")
        Location.add_root(name="Unknown", location_type="facility")
        location_ct += 1

    print(f"added {location_ct} new locations to system")
    print(f"updated {update_ct} locations with new data")


# combine fields ending with _other with their normal counterparts (e.x. Id10010_other, Id10010).
# in Zambia data, often either the normal or _other field has a value but not both.
# NOTE: currently using 'cleaned' version of other field (called filtered_<field>_other)
# and discarding <field>-other values. verify that this is kosher.
def deduplicate_columns(record_df, drop_duplicates=True):
    other_cols = record_df.filter(regex=r"\_other$", axis=1).columns
    # get original columns that other columns are derived from
    original_cols = list(
        set(
            other_cols.str.replace(r"^filtered\_", "", regex=True)
            .str.replace(r"_other$", "", regex=True)
            .tolist()
        )
    )
    for original_col in original_cols:

        # If original column exists, combine values from original and _other columns into a single column
        if original_col in record_df.columns:
            record_df[original_col] = (
                record_df.filter(regex=original_col, axis=1)
                .replace("other", np.nan)
                .bfill(axis=1)
                .iloc[:, 0]
            )
            # record_df[original_col] = record_df.apply(lambda row: row[other_col]
            # f pd.isnull(row[original_col]) else row[original_col], axis=1)
        else:
            print(
                f"WARNING: couldn't find {original_col} but {original_col}_other in columns"
            )
    if drop_duplicates:
        record_df = record_df.drop(columns=other_cols)
    return record_df


def get_va_summary_stats(vas, filter_fields=False):
    # calculate stats
    if vas.count() > 0:

        # if filter_fields=True, filter down to only relevant fields
        if filter_fields:
            vas = vas.only("created", "id", "location", "Id10023")

        stats = vas.aggregate(
            last_update=Max("created"),
            last_submission=Max("submissiondate"),
            total_vas=Count("id"),
        )

        stats["ineligible_vas"] = vas.filter(
            Q(Id10023__in=["DK", "dk"])
            | Q(Id10023__isnull=True)
            | Q(location__isnull=True)
        ).count()

        # clean up dates if non-null
        if stats["last_update"] and type(stats["last_update"]) is not str:
            stats["last_update"] = stats["last_update"].strftime("%Y-%m-%d")

        if stats["last_submission"] and type(stats["last_update"]) is not str:
            stats["last_submission"] = stats["last_submission"].strftime("%Y-%m-%d")
        return stats
    # no VAs - return empty stats
    else:
        return {
            "last_update": None,
            "last_submission": None,
            "total_vas": None,
            "ineligible_vas": None,
        }
