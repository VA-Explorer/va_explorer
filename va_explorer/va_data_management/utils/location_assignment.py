import re

import pandas as pd
from fuzzywuzzy import fuzz

from va_explorer.va_data_management.models import Location, VaUsername


def build_location_mapper(
    va_locations,
    db_locations=None,
    loc_type="facility",
    drop_terms=None,
    similarity_thresh=75,
    prnt=False,
):
    if va_locations and len(va_locations) > 0:
        # store database locations of type location_type in a df
        if not db_locations:
            db_locations = list(
                Location.objects.filter(location_type=loc_type).values_list(
                    "name", flat=True
                )
            )
        location_df = pd.DataFrame({"name": db_locations}).assign(
            key=lambda df: df["name"].str.lower()
        )

        # store unique va_locations in mapper dataframe
        va_locations = list(set(va_locations).difference(set(["other"])))
        mapper = pd.DataFrame({"va_name": va_locations}).dropna()
        if not mapper.empty:
            mapper["va_key"] = (
                mapper["va_name"].str.lower().replace(r"\_", " ", regex=True)
            )

            # preprocess dataframes
            if not drop_terms:
                drop_terms = ["general", "central", "teaching"]

            for term in drop_terms:
                location_df["key"] = location_df["key"].replace(
                    f" {term}", "", regex=True
                )
                mapper["va_key"] = mapper["va_key"].replace(f" {term}", "", regex=True)

            # matching
            mapper["db_name"] = mapper["va_key"].apply(
                lambda x: fuzzy_match(
                    x, option_df=location_df, threshold=similarity_thresh
                )
            )

            return mapper.set_index("va_name")["db_name"].to_dict()
    if prnt:
        print("WARNING: no va locations provided, returning empty dict")
    return {}


def assign_va_location(va, location_mapper=None, location_fields=None):
    # check if the hospital or place of death fields are known locations
    location_fields = (
        ["hospital", "hospital_other"] if not location_fields else location_fields
    )
    raw_location, db_location = None, None
    for location_field in location_fields:
        raw_location = va.__dict__.get(location_field, None)
        if raw_location:
            break
    if raw_location:
        if not location_mapper:
            location_mapper = build_location_mapper([raw_location])
        db_location_name = location_mapper.get(raw_location, None)
        # if matching db location, retrive it. Otherwise, record location as unknown
        if db_location_name:
            # TODO: make this more generic to other location hierarchies
            db_location = Location.objects.filter(
                location_type="facility", name=db_location_name
            ).first()

    # if no db location found, and va username defined, try setting username's location
    if not db_location:
        if va.username:
            if len(va.username) > 0:
                va_user = VaUsername.objects.filter(va_username=va.username).first()
                if va_user:
                    user_locations = va_user.user.location_restrictions
                    if user_locations:
                        db_location = user_locations.first()

    # if any db location found, update VA with found location
    if db_location:
        va.location = db_location
    elif not pd.isnull(raw_location):
        if len(raw_location) > 0 and raw_location.lower() not in ["dk", "nan"]:
            # if raw location detected but no db match, set to "Unknown"
            va.set_null_location()
    # otherwise, va.location will just be blank
    return va


def fuzzy_match(
    search,
    options=None,
    option_df=pd.DataFrame(),
    threshold=75,
    preprocess=False,
    drop_terms=None,
    prnt=False,
    return_str=True,
):
    match = None
    if not pd.isnull(search):
        if not options and option_df.size == 0:
            raise ValueError(
                "Please provide an option list or option_df (dataframe with options in 'name' column)"
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
        # if preprocess=True, clean search term and options before comparing
        search_term = search
        if preprocess:
            if not drop_terms:
                drop_terms = ["general", "central", "teaching"]

            search_term = re.sub(r"\_", " ", search.lower())
            for term in drop_terms:
                search_term = search_term.replace(f" {term}", "")
                option_df["key"] = option_df["key"].replace(f" {term}", "", regex=True)

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
            if return_str:
                # just return matching name
                match = option_df.iloc[0]["name"]
            else:
                # return all data about match
                match = option_df.iloc[0, :].to_dict()

    return match
