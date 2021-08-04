#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Apr 13 10:08:05 2021

@author: babraham
"""

from django.db.models import IntegerField
from django.db.models.functions import Cast
from django.db.models import F
import pandas as pd
import numpy as np
import json
import os
import time

from va_explorer.va_data_management.models import Location
from va_explorer.va_data_management.utils.loading import get_va_summary_stats

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
    ti = time.time()
    # the dashboard requires date of death, exclude if the date is unknown
    # Using .values at the end lets us do select_related("causes") which drastically speeds up the query.
    user_vas = user.verbal_autopsies(date_cutoff=date_cutoff)
    cur_time=time.time(); print(f"time for raw va query: {cur_time - ti} secs"); ti=cur_time
    # get stats on last update and last va submission date
    update_stats = get_va_summary_stats(user_vas)
    cur_time=time.time(); print(f"time to calc va stats: {cur_time - ti} secs"); ti=cur_time
    all_vas = user_vas\
        .only(
            "id",
            "Id10019", # gender
            "Id10058", # place of death
            "Id10023", # date of death
            "ageInYears",
            "age_group",
            "isNeonatal1",
            "isChild1",
            "isAdult1",
            "location", # facility VA is tied to
            "Id10010" # field worker
        ) \
        .exclude(Id10023="dk") \
        .exclude(location__isnull=True) \
        .select_related("location") \
        .select_related("causes") \
        .values(
            "id",
            "Id10019",
            "Id10058",
            "age_group",
            "isNeonatal1",
            "isChild1",
            "isAdult1",
            'location__id',
            'location__name',
            'ageInYears',
            "Id10010",
            date=F("Id10023"),
            cause=F("causes__cause"),
        )
    
    if not all_vas:
        return {"data": {"valid": pd.DataFrame(), "invalid": pd.DataFrame()}, "update_stats": {update_stats}}

    cur_time=time.time(); print(f"time va join: {cur_time - ti} secs"); ti=cur_time
    # Build a dictionary of location ancestors for each facility
    # TODO: This is not efficient (though it"s better than 2 DB queries per VA)
    # TODO: This assumes that all VAs will occur in a facility, ok? 
    # TODO: if there is no location data, we could use the location associated with the interviewer
#    location_types = dict()
    location_types = dict(list(set(Location.objects.exclude(name='Unknown').values_list('depth', 'location_type'))))
    # assuming VA location type is lowest rung of location tree hierarchy
    va_location_type = location_types[len(location_types)]
    # Non-POI locations (geographies)
    locations = {}
    facilities = Location.objects.filter(location_type="facility")
    location_ancestors = {
        location.id: location.get_ancestors()
        for location in facilities
    }
    cur_time=time.time(); print(f"time to build ancestor table: {cur_time - ti} secs"); ti=cur_time
    for va in all_vas:
        # add location's category to dataframe. Assumes tagged location is lowest depth of location tree.
        va[va_location_type] = va["location__name"]
        # Find parents (likely district and province).
        for ancestor in location_ancestors[va['location__id']]:
            va[ancestor.location_type] = ancestor.name
            #location_types.add(ancestor.location_type)
            #location_types[ancestor.depth] = ancestor.location_type
            location_data = {}
            locations[ancestor.name] = ancestor.location_type #{field: getattr(ancestor, field) for field in common_location_fields}

        # Clean up location fields.
        va["location"] = va["location__name"]
        del va["location__name"]
        del va["location__id"]
    cur_time=time.time(); print(f"time to process vas: {cur_time - ti} secs"); ti=cur_time

    # POI locations (hospitals/facilities). Only populate if lat/lons found in database
    # look for these fields in location POI data. Will only pull in these fields if found in Location DB schema
    dashboard_poi_fields = {'id', 'name', 'location_type', 'lat', 'lon'}
    db_poi_fields = set([field.name for field in Location._meta.get_fields()])
    common_poi_fields = dashboard_poi_fields.intersection(db_poi_fields)

    pois = {}
    any_coordinates = any(map(lambda x: getattr(x, "lat") is not None, facilities))
    if any_coordinates:
        for poi in facilities.values(*common_poi_fields):
            # only add POI if it has ancestors
            poi_ancestors = location_ancestors.get(poi["id"], None)
            if poi_ancestors:
                # add poi parent (last object in ancestor list)
                poi["parent"] = list(poi_ancestors)[-1].name
                # poi depth = 1 + number of ancestors it has
                poi_depth = poi_ancestors.count() + 1
                # record poi's location type
                location_types[poi_depth] = poi["location_type"]
                # record poi's data (coordinates)
                pois[poi["name"]] = poi 
    # Convert VA list to dataframe.
    va_df = pd.DataFrame.from_records(all_vas)
    cur_time=time.time(); print(f"time to process pois: {cur_time - ti} secs"); ti=cur_time
    
    # convert dates to datetimes
    va_df["date"] = pd.to_datetime(va_df["date"])
    va_df["age"] = pd.to_numeric(va_df["ageInYears"], errors="coerce")
    va_df["age_group"] = assign_age_groups(va_df)
    cur_time=time.time(); print(f"time to clean fields: {cur_time - ti} secs"); ti=cur_time

    # need this becasue location types need to be sorted by depth
    location_types = [
        l for _, l in sorted(location_types.items(), key=lambda x: x[0])
    ]
    
    return {
        "data": {
            "valid": va_df[~pd.isnull(va_df["cause"])].reset_index(),
            "invalid": va_df[pd.isnull(va_df["cause"])].reset_index(),
        },
        "location_types": location_types,
        "pois": pois,
        "max_depth": len(location_types) - 1,
        "locations": locations,
        "update_stats": update_stats
    }

# row-wise age group assignment logic
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
    except:
        return "Unknown"

# faster version of assign_age_group for matrix/dataframe instead of just one row
def assign_age_groups(va_df):
    groups = set(['adult', 'neonate', 'child'])
    va_df['age'] = va_df['age'].astype(float)
    age_groups = np.where(va_df["age_group"].isin(groups), va_df['age_group'],\
        np.where(va_df['isNeonatal1'] == 1, 'neonate', \
            np.where(va_df['isChild1'] == 1, 'child', \
                np.where(va_df['isAdult1']==1, 'adult', \
                    np.where(pd.isnull(va_df['age']), 'Unknown', \
                        np.where(va_df['age'] <= 1, 'neonate', \
                            np.where(va_df['age'] <= 16, 'child', 'adult')))))))
    return age_groups

