import csv
import itertools
import json
import os
from operator import itemgetter
from pathlib import Path

import pandas as pd
from django.db.models import F, Q, Case, When, Value, DateField, CharField, Count, Subquery, OuterRef
from django.db.models.functions import Cast, TruncMonth, Substr

from va_explorer.va_data_management.models import Location, questions_to_autodetect_duplicates
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


def load_cod_groupings(cause_of_death: str):
    filename = 'cod_groupings.csv'
    path = Path(__file__).parent.parent / 'data' / filename

    with open(path) as csvfile:
        filereader = csv.DictReader(csvfile)
        remove = ['algorithm', 'cod']
        headers = [header for header in filereader.fieldnames if header not in remove]

        data = []
        for row in filereader:
            data.append(row)

        cods = sorted([row.get('cod') for row in data] + headers)

    filter_causes = []
    if cause_of_death:
        for row in data:
            if row.get('cod') == cause_of_death:
                filter_causes.append(row.get('cod'))
                break

            for key, value in row.items():
                if cause_of_death == key and value == '1':
                    filter_causes.append(row.get('cod'))

    return {'dropdown_options': cods, 'filter_causes': filter_causes}


# ============ VA Data =================
def load_va_data(user, cause_of_death, start_date, end_date, region_of_interest):
    user_vas = user.verbal_autopsies(date_cutoff=start_date, end_date=end_date)

    # get stats on last update and last va submission date
    update_stats = get_va_summary_stats(user_vas)
    if len(questions_to_autodetect_duplicates()) > 0:
        update_stats["duplicates"] = user_vas.filter(duplicate=True).count()

    user_vas_filtered = (user_vas
                         .exclude(Id10023__in=["dk", "DK"])
                         .exclude(location__isnull=True)
                         )

    if cause_of_death:
        causes = load_cod_groupings(cause_of_death=cause_of_death)['filter_causes']
        user_vas_filtered = user_vas_filtered.filter(causes__cause__in=causes)

    if region_of_interest:
        if "District" in region_of_interest:
            user_vas_filtered = (
                user_vas_filtered.annotate(district_name=Subquery(Location.objects.values('name').filter(
                    Q(path=Substr(OuterRef("location__path"), 1, 8)), Q(depth=2))[:1]))
                .filter(district_name=region_of_interest)
                .select_related("location")
            )

        if "Province" in region_of_interest:
            user_vas_filtered = (
                user_vas_filtered.annotate(province_name=Subquery(Location.objects.values('name').filter(
                    Q(path=Substr(OuterRef("location__path"), 1, 4)), Q(depth=1))[:1]))
                .filter(province_name=region_of_interest)
                .select_related("location")
            )

    uncoded_vas = user_vas.filter(causes__cause__isnull=True).count()

    demographics = (
        user_vas_filtered
        .filter(causes__isnull=False)
        .values(gender=F('Id10019'), age_group_named=Case(When(isNeonatal1='1', then=Value('neonate')),
                                                          When(isChild1='1', then=Value('child')),
                                                          When(isAdult1='1', then=Value('adult')),
                                                          When(ageInYears__lte=1, then=Value('neonate')),
                                                          When(ageInYears__lte=16, then=Value('child')),
                                                          default=Value('Unknown'), output_field=CharField()
                                                          ))
        .annotate(count=Count('pk'))
        .order_by('age_group_named')
    )

    demographics = [
        {'age_group': key, **{item.get('gender'): item.get('count') for item in list(group)}}
        for key, group in itertools.groupby(demographics, itemgetter('age_group_named'))
    ]

    COD_sums = (
        user_vas_filtered
        .filter(causes__isnull=False)
        .select_related("causes")
        .values(cause=F("causes__cause"))
        .annotate(count=Count('pk'))
        .order_by('-count')
    )

    COD_trend = (
        user_vas_filtered
        .annotate(month=TruncMonth(Cast('Id10023', output_field=DateField())))
        .filter(causes__isnull=False)
        .values('month')
        .annotate(count=Count('pk'))
        .order_by('month')
    )

    place_of_death = (
        user_vas_filtered
        .filter(causes__isnull=False)
        .values(place=F('Id10058'))
        .annotate(count=Count('pk'))
        .order_by('-count')
    )

    geographic_province_sums = (
        user_vas_filtered
        .annotate(province_name=Subquery(
            Location.objects.values('name').filter(Q(path=Substr(OuterRef("location__path"), 1, 4)), Q(depth=1))[:1]
        ))
        .select_related("location")
        .values("province_name")
        .annotate(count=Count('pk'))
    )

    geographic_district_sums = (
        user_vas_filtered
        .annotate(district_name=Subquery(
            Location.objects.values('name').filter(Q(path=Substr(OuterRef("location__path"), 1, 8)), Q(depth=2))[:1]
        ))
        .select_related("location")
        .values("district_name")
        .annotate(count=Count('pk'))
    )

    data = {
        "COD_grouping": COD_sums,
        "COD_trend": COD_trend,
        "place_of_death": place_of_death,
        "demographics": demographics,
        "geographic_province_sums": geographic_province_sums,
        "geographic_district_sums": geographic_district_sums,
        "uncoded_vas": uncoded_vas,
        "update_stats": update_stats,
        "all_causes_list": load_cod_groupings(cause_of_death=cause_of_death)['dropdown_options']
    }

    return data
