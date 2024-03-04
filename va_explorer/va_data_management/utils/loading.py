import logging
import random

import numpy as np
import pandas as pd
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.db.models import Count, Max, Q
from simple_history.utils import bulk_create_with_history

from va_explorer.users.utils.demo_users import make_field_workers_for_facilities
from va_explorer.va_data_management.models import Location, VerbalAutopsy
from va_explorer.va_data_management.utils.date_parsing import parse_date
from va_explorer.va_data_management.utils.location_assignment import (
    assign_va_location,
)
from va_explorer.va_data_management.utils.validate import validate_vas_for_dashboard

from ..constants import _checkbox_choices

User = get_user_model()


# load VA records into django database
def load_records_from_dataframe(record_df, random_locations=False, debug=False):
    logger = None if not debug else logging.getLogger("debug")
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

    # But first, account for case differences in csv columns
    # (i.e. ensure id10041 maps to Id10041)
    field_case_mapper = {field.lower(): field for field in model_field_names}
    record_df = record_df.rename(columns=lambda c: field_case_mapper.get(c.lower(), c))

    # instanceid is an essential identifier. Normalize input if needed and
    # attempt some known workarounds for supported integrations if such an
    # important field happens to be missing.
    if "instanceID" in record_df.columns:
        record_df = record_df.rename(columns={"instanceID": "instanceid"})
    if "instanceid" not in record_df.columns and "key" in record_df.columns:
        record_df = record_df.rename(columns={"key": "instanceid"})  # ODK
    elif "instanceid" not in record_df.columns and "_uuid" in record_df.columns:
        record_df = record_df.rename(columns={"_uuid": "instanceid"})  # Kobo

    # similar story for instancename. normalized, less known workarounds. if record
    # does not at least have first/last name for deceased (Id10017 + Id10018) and an
    # interview date (Id10012), consider it unrecoverable and drop from import
    invalid_vas = []
    if "instanceName" in record_df.columns:
        record_df = record_df.rename(columns={"instanceName": "instancename"})
    elif "instancename" not in record_df.columns:
        record_df["instancename"] = None

    unrecoverable = record_df[
        record_df["Id10017"].isnull()
        | record_df["Id10018"].isnull()
        | record_df["Id10012"].isnull()
    ]
    invalid_vas.extend(unrecoverable.iterrows())
    record_df.drop(labels=unrecoverable.index.values, axis=0)

    missing_instancenames = record_df[record_df["instancename"].isnull()]
    corrected_vas = []
    for index, record in missing_instancenames.iterrows():
        instancename = f"_Dec---{record['Id10017']} {record['Id10018']}_D.o.I---{record['Id10012']}"  # noqa: E501
        record_df.at[index, "instancename"] = instancename
        corrected_vas.append(index)
    record_df["instancename"] = record_df["instancename"].str.casefold()

    # Patch VAs that are missing Id10010 (Interviewer Name) with custom field fallbacks
    if "Id10010" not in record_df.columns and "SubmitterName" in record_df.columns:
        record_df = record_df.rename(columns={"SubmitterName": "Id10010"})  # ODK
    elif "Id10010" not in record_df.columns and "_submitted_by" in record_df.columns:
        record_df = record_df.rename(columns={"_submitted_by": "Id10010"})  # Kobo

    # Kobo provides an indicator for which records are invalid. Check if this
    # column is present, and if so, drop these from import consideration plus
    # attempt to remove them from existing VA Explorer records
    invalid_vas = []
    if "_validation_status" in record_df.columns:
        filtered_df = record_df[
            record_df["_validation_status"].apply(
                lambda x: isinstance(x, dict) and len(x) != 0
            )
        ]  # Assume blank/not indicated is fine
        invalid = filtered_df[
            filtered_df["_validation_status"].apply(
                lambda x: x["label"] in (["On Hold", "Not Approved"])
            )
        ]
        invalid_uuids = invalid["instanceid"].to_list() if len(invalid) > 0 else []
        to_remove = VerbalAutopsy.objects.filter(instanceid__in=invalid_uuids)
        for va in to_remove:
            invalid_vas.append(va)
        to_remove.delete()
        record_df = record_df.drop(labels=invalid.index.values, axis=0)

    print("de-duplicating fields...")
    # collapse fields ending with _other for their normal counterparts
    # (e.x. Id10010_other, Id10010)
    record_df = deduplicate_columns(record_df)

    csv_field_names = record_df.columns
    common_field_names = csv_field_names.intersection(model_field_names)

    # Only keep fields in CSV that we have columns for in our VerbalAutopsy model
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
    outdated_vas = []
    created_vas = []
    location_map = {}

    # build location mapper to map csv locations to known db locations
    if "hospital" in record_df.columns:
        hospitals = record_df["hospital"].unique().tolist()
        location_map = {
            key_name_pair[0]: key_name_pair[1]
            for key_name_pair in Location.objects.filter(key__in=hospitals)
            .only("name", "key")
            .values_list("key", "name")
        }

    # if random locations, assign random locations via a random field worker.
    if random_locations:
        field_workers = [u for u in User.objects.all() if u.is_fieldworker()]
        if len(field_workers) <= 1:
            print(
                "WARNING: no field workers in system. \
                Generating random ones now..."
            )
            make_field_workers_for_facilities()
            field_workers = [u for u in User.objects.all() if u.is_fieldworker()]

    # pull in all existing VA instanceIDs from db for de-duping purposes
    print("pulling in instance ids...")
    va_instance_ids = set(VerbalAutopsy.objects.values_list("instanceid", flat=True))
    va_instance_names = set(
        VerbalAutopsy.objects.values_list("instancename", flat=True)
    )

    if debug:
        print(
            f"# of VAs: {record_df.shape[0]}, \
            # of instanceIDs: {record_df.instanceid.nunique()}, \
            # of instanceNames: {record_df.instancename.nunique()}"
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
                # If VA "doesn't exist", it's still possible we have an edited VA,
                # since kobo will change the uuid for an edited VA. Check if a
                # previous instancename for this "new" VA exists and if so, delete
                # the old one in favor of this new one
                if row["instancename"] in va_instance_names:
                    outdated_va = VerbalAutopsy.objects.filter(
                        instancename=row["instancename"]
                    )
                    outdated_vas.append(outdated_va)
                    outdated_va.delete()

                va_instance_ids.add(row["instanceid"])

        # If we got here, we have a new, legit VA on our hands.
        va_id = row.get("instanceid", f"{i} of {record_df.shape[0]}")

        # Try to parse date of death as as datetime. Otherwise, record string and
        # add record issue during validation
        parsed_date = parse_date(va.Id10023, strict=False)
        if logger:
            logger.info(
                "va_id: %s - Parsed %s for Date of Death from %s",
                va_id,
                parse_date,
                va.Id10023,
            )
        va.Id10023 = parsed_date

        # Try to parse interview date as as datetime. Otherwise, record string and
        # add record issue during validation
        parsed_sub_date = parse_date(va.Id10012, strict=False)
        if logger:
            logger.info(
                "va_id: %s - Parsed %s as Interview Date from %s",
                va_id,
                parsed_sub_date,
                va.Id10012,
            )
        va.Id10012 = parsed_sub_date

        # if random_locations, assign random field worker to VA which can be used
        # to determine location.
        # Otherwise, try assigning location based on hospital field.
        if random_locations:
            user = random.choice(field_workers)
            va.location = user.location_restrictions.first()
        else:
            assign_va_location(va, location_map)
            if "hospital" in row and logger:
                logger.info(
                    "va_id: %s - Matched hospital %s to %s location in DB",
                    va_id,
                    row["hospital"],
                    va.location,
                )

        # Generate a unique_identifier_hash for each VA if the application is
        # configured to detect duplicate VAs
        if VerbalAutopsy.auto_detect_duplicates():
            va.generate_unique_identifier_hash()
        created_vas.append(va)

    print("populating DB...")
    new_vas = bulk_create_with_history(created_vas, VerbalAutopsy)

    print("Validating VAs...")
    # Add any errors to the db
    validate_vas_for_dashboard(new_vas)

    # Mark duplicate VAs if the application is configured to do so
    if VerbalAutopsy.auto_detect_duplicates():
        print("Marking VAs as duplicate...")
        VerbalAutopsy.mark_duplicates()

    return {
        "ignored": ignored_vas,
        "outdated": outdated_vas,
        "created": created_vas,
        "corrected": corrected_vas,
        "removed": invalid_vas,
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


# combine fields ending with _other for their normal counterparts
# (e.x. Id10010_other, Id10010).
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
        # If original column exists, combine values from original and _other
        # columns into a single column
        if original_col in record_df.columns:
            record_df[original_col] = (
                record_df.filter(regex=original_col, axis=1)
                .replace("other", np.nan)
                .bfill(axis=1)
                .iloc[:, 0]
            )
            # record_df[original_col] = record_df.apply(lambda row: row[other_col]
            # f pd.isna(row[original_col]) else row[original_col], axis=1)
        else:
            print(
                f"WARNING: couldn't find {original_col} but \
                {original_col}_other in columns"
            )
    if drop_duplicates:
        record_df = record_df.drop(columns=other_cols)
    return record_df


def get_va_summary_stats(vas, filter_fields=False):
    # if vas.count() > 0 code is the slowest SQL query

    # if filter_fields=True, filter down to only relevant fields
    if filter_fields:
        vas = vas.only("created", "id", "location", "Id10023")

    # check cache for va summary stats and set it if not already there
    stats = cache.get("va_summary_stats")
    if not stats:
        stats = vas.aggregate(
            last_update=Max("created"),
            last_interview=Max("Id10012"),
            total_vas=Count("id"),
        )
        cache.set("va_summary_stats", stats, timeout=60 * 60)

    stats["ineligible_vas"] = vas.filter(
        Q(Id10023__in=["DK", "dk"]) | Q(Id10023__isnull=True) | Q(location__isnull=True)
    ).count()

    # clean up dates if non-null
    if stats["last_update"] and not isinstance(stats["last_update"], str):
        stats["last_update"] = stats["last_update"].strftime("%Y-%m-%d")

    if stats["last_interview"]:
        # Handle datetimes and Text (which can occur since interview is TextField)
        if not isinstance(stats["last_interview"], str):
            stats["last_interview"] = stats["last_interview"].strftime("%Y-%m-%d")
        else:
            stats["last_interview"] = parse_date(stats["last_interview"])
    return stats
    # TODO is it likely or possible to return no VAs? if yes, return empty stats
