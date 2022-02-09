import json
import os

import pandas as pd
from django.db.models import F

from va_explorer.va_data_management.models import Location
from va_explorer.va_data_management.utils.loading import get_va_summary_stats


# ============ GEOJSON Data (for map) =================
# load geojson data from flat file (will likely migrate to a database later)
def load_geojson_data(json_file):
    geojson = None
    if os.path.isfile(json_file):
        with open(json_file, "r") as jf:
            geojson = json.loads(jf.read())

        # add min and max coordinates for mapping
        for i, g in enumerate(geojson["features"]):
            coordinate_list = g["geometry"]["coordinates"]
            coordinate_stat_tables = []
            for coords in coordinate_list:
                if len(coords) == 1:
                    coords = coords[0]
                coordinate_stat_tables.append(
                    pd.DataFrame(coords, columns=["lon", "lat"]).describe()
                )
            g["properties"]["area_name"] += " {}".format(
                g["properties"]["area_level_label"]
            )
            g["properties"]["min_x"] = min(
                [stat_df["lon"]["min"] for stat_df in coordinate_stat_tables]
            )
            g["properties"]["max_x"] = max(
                [stat_df["lon"]["max"] for stat_df in coordinate_stat_tables]
            )
            g["properties"]["min_y"] = min(
                [stat_df["lat"]["min"] for stat_df in coordinate_stat_tables]
            )
            g["properties"]["max_y"] = max(
                [stat_df["lat"]["max"] for stat_df in coordinate_stat_tables]
            )
            geojson["features"][i] = g
        # save total districts and provinces for future use
        geojson["district_count"] = len(
            [
                f
                for f in geojson["features"]
                if f["properties"]["area_level_label"] == "District"
            ]
        )
        geojson["province_count"] = len(
            [
                f
                for f in geojson["features"]
                if f["properties"]["area_level_label"] == "Province"
            ]
        )
    return geojson


# ============ VA Data =================
def load_va_data(user, geographic_levels=None, date_cutoff="1901-01-01"):
    # the dashboard requires date of death, exclude if the date is unknown
    # Using .values at the end lets us do select_related("causes") which drastically speeds up the query.
    user_vas = user.verbal_autopsies(date_cutoff=date_cutoff)
    # get stats on last update and last va submission date
    update_stats = get_va_summary_stats(user_vas)
    all_vas = (
        user_vas.only(
            "id",
            "Id10019",
            "Id10058",
            "Id10023",
            "ageInYears",
            "age_group",
            "isNeonatal1",
            "isChild1",
            "isAdult1",
            "location",
        )
        .exclude(Id10023__in=["dk", "DK"])
        .exclude(location__isnull=True)
        .select_related("location")
        .select_related("causes")
        .values(
            "id",
            "Id10019",
            "Id10058",
            "age_group",
            "isNeonatal1",
            "isChild1",
            "isAdult1",
            "location__id",
            "location__name",
            "ageInYears",
            date=F("Id10023"),
            cause=F("causes__cause"),
        )
    )

    if not all_vas:
        return json.dumps(
            {
                "data": {
                    "valid": pd.DataFrame().to_json(),
                    "invalid": pd.DataFrame().to_json(),
                },
                "update_stats": {update_stats},
            }
        )

    # Build a dictionary of location ancestors for each facility
    # TODO: This is not efficient (though it"s better than 2 DB queries per VA)
    # TODO: This assumes that all VAs will occur in a facility, ok?
    # TODO: if there is no location data, we could use the location associated with the interviewer
    location_types = dict()
    locations = {}
    location_ancestors = {
        location.id: location.get_ancestors()
        for location in Location.objects.filter(location_type="facility")
    }

    for va in all_vas:
        # Find parents (likely district and province).
        for ancestor in location_ancestors[va["location__id"]]:
            va[ancestor.location_type] = ancestor.name
            # location_types.add(ancestor.location_type)
            location_types[ancestor.depth] = ancestor.location_type
            locations[ancestor.name] = ancestor.location_type

        # Clean up location fields.
        va["location"] = va["location__name"]
        del va["location__name"]
        del va["location__id"]

    # Convert list to dataframe.
    va_df = pd.DataFrame.from_records(all_vas)
    # convert dates to datetimes
    va_df["date"] = pd.to_datetime(va_df["date"])
    va_df["age"] = pd.to_numeric(va_df["ageInYears"], errors="coerce")
    va_df["age_group"] = va_df.apply(assign_age_group, axis=1)

    # need this because location types need to be sorted by depth
    location_types = [l for _, l in sorted(location_types.items(), key=lambda x: x[0])]

    return {
        "data": {
            "valid": va_df[~pd.isnull(va_df["cause"])].reset_index(),
            "invalid": va_df[pd.isnull(va_df["cause"])].reset_index(),
        },
        "location_types": location_types,
        "max_depth": len(location_types) - 1,
        "locations": locations,
        "update_stats": update_stats,
    }


def assign_age_group(va):
    # If age group is unassigned, determine age group by age group fields first, then age number, otherwise mark NA
    # TODO determine if this is a valid check for empty or unknown values

    if va["age_group"] in ["adult", "neonate", "child"]:
        return va["age_group"]

    if va["isNeonatal1"] == 1:
        return "neonate"

    if va["isChild1"] == 1:
        return "child"

    if va["isAdult1"] == 1:
        return "adult"

    # try determine group by the age in years
    try:
        age = int(float(va["age"]))
        if age <= 1:
            return "neonate"
        if age <= 16:
            return "child"
        return "adult"
    # Intent is to assign unknown
    except:  # noqa E722
        return "Unknown"
