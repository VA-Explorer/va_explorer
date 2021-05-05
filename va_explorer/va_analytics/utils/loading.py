#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Apr 13 10:08:05 2021

@author: babraham
"""


import pandas as pd
import numpy as np
import json
import os
import time

from va_explorer.va_data_management.models import Location

# ============ GEOJSON Data (for map) =================
# load geojson data from flat file (will likely migrate to a database later)
def load_geojson_data(json_file):
    geojson = None
    if os.path.isfile(json_file):

        raw_json = open(json_file, "r")
        geojson = json.loads(raw_json.read())
        raw_json.close()
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
    np.random.seed(23)
    return_dict = {"data": {"valid": pd.DataFrame(), "invalid": pd.DataFrame()}}
    
    # the dashboard requires date of death, exclude if the date is unknown
    all_vas = user.verbal_autopsies(date_cutoff=date_cutoff).exclude(Id10023="dk").exclude(location__isnull=True).prefetch_related("location").prefetch_related("causes")
    
    if len(all_vas) > 0:
        # Grab exactly the fields we need, including location and cause data
        va_data = [
            {
                "id": va.id,
                "Id10019": va.Id10019,
                "Id10058": va.Id10058,
                "date" : va.Id10023, # date of death assignment
                "ageInYears": va.ageInYears,
                "age_group": va.age_group,
                "isNeonatal1": va.isNeonatal1,
                "isChild1": va.isChild1,
                "isAdult1": va.isAdult1,
                "location": va.location.name,
                "cause": va.causes.first()
            }
            for va in all_vas
        ]

        # Build a location ancestors lookup and add location information at all levels to all vas
        # TODO: This is not efficient (though it's better than 2 DB queries per VA)
        # TODO: This assumes that all VAs will occur in a facility, ok? 
        # TODO: if there is no location data, we could use the location associated with the interviewer
        locations, location_types = dict(), dict()
        location_ancestors = {
            location.id: location.get_ancestors()
            for location in Location.objects.filter(location_type="facility")
        }
        for i, va in enumerate(all_vas):
            #            location_types[va.location.depth] = va.location.location_type
            #            locations.add(va.location.name)
            for ancestor in location_ancestors[va.location.id]:
                va_data[i][ancestor.location_type] = ancestor.name
                location_types[ancestor.depth] = ancestor.location_type
                locations[ancestor.name] = ancestor.location_type
        va_df = pd.DataFrame.from_records(va_data)

        # Set the age field so we can calculate mean age of death
        va_df["age"] = pd.to_numeric(va_df["ageInYears"], errors="coerce")

        # Assign to age group
        va_df["age_group"] = va_df.apply(assign_age_group, axis=1)

        # split data into valid data (records w COD) and invalid records (recoreds w/out COD)
        valid_va_df = va_df[~pd.isnull(va_df["cause"])].reset_index()
        invalid_va_df = va_df[pd.isnull(va_df["cause"])].reset_index()
        # convert location_types to an ordered list
        location_types = [
            l for _, l in sorted(location_types.items(), key=lambda x: x[0])
        ]
        return_dict = {
            "data": {"valid": valid_va_df, "invalid": invalid_va_df},
            "location_types": location_types,
            "max_depth": len(location_types) - 1,
            "locations": locations,
        }

    return return_dict


def assign_age_group(va_row):
    # If age group is unassigned, determine age group by age group fields first, then age number, otherwise mark NA
    # TODO determine if this is a valid check for empty or unknown values
    if va_row["age_group"] not in ["adult", "neonate", "child"]: 
        if va_row["isNeonatal1"] == 1:
            return "neonate"
        elif va_row["isChild1"] == 1:
            return "child"
        elif va_row["isAdult1"] == 1:
            return "adult"
        else:
            # try determine group by the age in years
            try:
                age = int(va_row["age"])
                if age <= 1:
                    return "neonate"
                if age <= 16:
                    return "child"
                return "adult"
            except:
                return "Unknown"
    return va_row["age_group"]



