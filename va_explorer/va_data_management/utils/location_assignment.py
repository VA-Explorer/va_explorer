import pandas as pd
from fuzzywuzzy import fuzz

from va_explorer.va_data_management.models import Location


def assign_va_location(va, location_mapper=None, location_fields=None):
    # check if the hospital or place of death fields are known locations
    location_fields = (
        location_fields if location_fields else ["hospital", "hospital_other"]
    )
    raw_location, db_location = None, None
    for location_field in location_fields:
        raw_location = va.__dict__.get(location_field, None)
        if raw_location:
            break
    if raw_location:
        if not location_mapper:
            # no mapper provided, create a one-off for this assignment
            location_mapper = dict(
                Location.objects.filter(key=raw_location)
                .only("name", "key")
                .values_list("key", "name")
            )
        db_location_name = location_mapper.get(raw_location, None)
        # if matching db location, retrieve it. Otherwise, record location as unknown
        if db_location_name:
            # TODO: make this more generic to other location hierarchies
            db_location = Location.objects.filter(
                location_type="facility", name=db_location_name
            )
            if len(db_location) > 1:
                # attempt to find specific facility based on match with other
                # va location data. warn if that doesn't narrow it down completely
                search_string = (
                    f"{va.province} Province/{va.area} District/{va.hospital}"
                )
                db_location = db_location.filter(path_string__icontains=search_string)
                if len(db_location) > 1:
                    print(
                        f"WARNING: ambiguous location: {search_string} "
                        + "using most likely match"
                    )
            # need to take first anyway to get (ideally 1) Location out of QuerySet
            db_location = db_location.first()

    # if any db location found, update VA with found location
    if db_location:
        va.location = db_location
    elif (
        not pd.isna(raw_location)
        and len(raw_location) > 0
        and raw_location.lower() not in ["dk", "nan"]
    ):
        # if raw location detected but no db match, set to "Unknown"
        va.set_null_location()
    # otherwise, va.location will just be blank
    return va


def fuzzy_match(
    search,
    option_df,
    options=None,
    threshold=75,
    prnt=False,
    return_str=True,
):
    option_df = pd.DataFrame() if option_df is None else option_df
    match = None
    if not pd.isna(search):
        if not options and option_df.size == 0:
            raise ValueError(
                "Please provide an option list or option_df (dataframe with \
                options in 'name' column)"
            )
        # if options not in dataframe format, create one to store them
        if option_df.size == 0:
            option_df = pd.DataFrame({"name": options})
        # make sure options are stored in 'name' column
        assert "name" in option_df.columns
        # if no key field in dataframe, create lowercase keys from options
        if "key" not in option_df.columns:
            option_df["key"] = option_df["name"].str.lower()
        # if threshold is a decimal, convert to percent
        if threshold > 0 and threshold <= 1:
            threshold = int(100 * threshold)
        search_term = search

        # matching
        option_df["score"] = option_df["key"].apply(
            lambda x: fuzz.ratio(search_term, x)
        )
        option_df = option_df.sort_values(by="score", ascending=False)

        if prnt:
            print(option_df.head())

        # filter to only matches exceeding threshold
        option_df = option_df.query("score >= @threshold")

        if prnt:
            print(option_df)

        if option_df.size > 0:
            match = (
                option_df.iloc[0]["name"]
                if return_str
                else option_df.iloc[0, :].to_dict()
            )

    return match
