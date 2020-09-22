#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jul 29 15:25:20 2020

@author: babraham
"""

import json
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc

import pandas as pd
import plotly.graph_objs as go
import plotly.figure_factory as ff
import os
import numpy as np
import datetime as dt

from django_plotly_dash import DjangoDash
from verbal_autopsy.models import Location, VerbalAutopsy
from django.forms.models import model_to_dict

import re

import time

# ================APP DEFINITION===============#
# NOTE: to include external stylesheets, set external_stylesheets parameter in constructor
# app = dash.Dash(__name__)  # Dash constructor
app = DjangoDash(name="va_dashboard", serve_locally=True, add_bootstrap_links=True)


# TODO: We should eventually move this mapping to someplace where it's more configurable
# ===========INITIAL CONFIG VARIABLES=============#
# initial timefraome for map data to display
INIT_TIMEFRAME = "1 year"
# folder where geojson is kept
JSON_DIR = "va_explorer/va_analytics/dash_apps/geojson"
# Zambia Geojson pulled from: https://adr.unaids.org/dataset/zambia-geographic-data-2019
JSON_FILE = "zambia_geojson.json"
# initial granularity
INITIAL_GRANULARITY = "district"
# ============Lookup dictionaries =================#


def load_lookup_dicts():
    lookup = dict()
    # dictionary mapping time labels to days (or all)
    lookup["time_dict"] = {"1 week": 7, "1 month": 30, "1 year": 365, "all": "all"}
    # dictionary mapping demographic variable names to corresponding VA survey columns
    lookup["demo_to_col"] = {
        "age group": "age_group",
        "sex": "Id10019",
        "place of death": "Id10058",
    }
    # colors used for plotting
    lookup["color_list"] = [
        "rgb(24,162,185)",
        "rgb(201,0,1)",
        "rgb(8,201,0)",
        "rgb(240,205,21)",
        "rgb(187,21,240)",
        "rgb(250,250,248)",
        "rgb(162,162,162)",
    ]
    # dictionary mapping raw map metrics to human-readable names
    lookup["metric_names"] = {
        "Total Deaths": "Total Deaths",
        "Mean Age of Death": "Mean Age of Death",
        "HIV/AIDS related death": "HIV/AIDS",
        "Diabetes mellitus": "Diabetes Mellitus",
        "Acute resp infect incl pneumonia": "Pneumonia",
        "Other and unspecified cardiac dis": "Other Cardiac",
        "Diarrhoeal diseases": "Diarrhoeal Diseases",
        "Other and unspecified neoplasms": "Unspecified Neoplasm",
        "Renal failure": "Renal Failure",
        "Liver cirrhosis": "Liver Cirrhosis",
        "Digestive neoplasms": "Digestive Neoplasm",
        "Other and unspecified infect dis": "Other",
    }
    # dictionary mapping place of death names to more human-readable names
    lookup["death_location_names"] = {
        "on_route_to_hospital_or_facility": "En Route to Facility",
        "DK": "Unknown",
        "other_health_facility": "Other Health Facility",
    }
    # formats for montly, weekly, and yearly dates
    lookup["date_display_formats"] = {
        "week": "%d/%m/%Y",
        "month": "%m/%Y",
        "year": "%Y",
    }

    return lookup


LOOKUP = load_lookup_dicts()


# =============Geo dictionaries and global variables ========#
# load geojson data from flat file (will likely migrate to a database later)
def load_geojson_data(json_file):
    geojson = None
    if os.path.isfile(json_file):

        geojson = json.loads(open(json_file, "r").read())
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
            g["properties"]["area_name"] += " {}".format(g["properties"]["area_level_label"]) 
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
    return geojson


GEOJSON = load_geojson_data(json_file=f"{JSON_DIR}/{JSON_FILE}")


# ============ VA Data =================
def load_va_data(geographic_levels=None):
    va_df = pd.DataFrame()

    valid_vas = VerbalAutopsy.objects.exclude(causes=None).prefetch_related("location").prefetch_related("causes")

    if len(valid_vas) > 0:
        # Grab exactly the fields we need, including location and cause data
        va_data = [
            {
                "id": va.id,
                "Id10019": va.Id10019,
                "Id10058": va.Id10058,
                "ageInYears": va.ageInYears,
                "location": va.location.name,
                "cause": va.causes.all()[0].cause, # Don't use first() to take advantage of the prefetch
            }
            for va in valid_vas
        ]

        # Build a location ancestors lookup and add location information at all levels to all vas
        # TODO: This is not efficient (though it's better than 2 DB queries per VA)
        # TODO: This assumes that all VAs will occur in a facility, ok?
        location_ancestors = { location.id:location.get_ancestors() for location in Location.objects.filter(location_type="facility") }
        for i, va in enumerate(valid_vas):
            for ancestor in location_ancestors[va.location.id]:
                va_data[i][ancestor.location_type] = ancestor.name

        va_df = pd.DataFrame.from_records(va_data)

        # clean up age fields and assign to age bin
        # TODO: This random age assignment needs to be correctly handled
        va_df["age"] = va_df["ageInYears"].replace(
            to_replace=["dk"], value=np.random.randint(1, 80)
        )
        va_df["age"] = pd.to_numeric(va_df["age"])
        va_df["age_group"] = va_df["age"].apply(assign_age_group)
        cur_date = dt.datetime.today()

        # TODO: This random date of death assignment needs to be correctly handled
        # NOTE: date field called -Id10023 in VA form, but no dates in curent responses
        va_df["date"] = [
            cur_date - dt.timedelta(days=int(x))
            for x in np.random.randint(3, 400, size=va_df.shape[0])
        ]

    return va_df


def assign_age_group(age):
    if age <= 1:
        return "neonate"
    elif age <= 16:
        return "child"
    else:
        return "adult"


# =========Map Metrics =======================#
# Top metrics to track for map dropdown
# TODO: these need to be loaded from the actual VA data in the DB via a callback
def get_metrics():
    metrics = [
        "Total Deaths",
        "Mean Age of Death",
        "HIV/AIDS related death",
        "Diabetes mellitus",
        "Acute resp infect incl pneumonia",
        "Other and unspecified cardiac dis",
        "Diarrhoeal diseases",
        "Other and unspecified neoplasms",
        "Renal failure",
        "Liver cirrhosis",
        "Digestive neoplasms",
        "Other and unspecified infect dis"
    ]
    return metrics


def get_metric_display_names(map_metrics):
    names = []
    for metric in map_metrics:
        metric_name = LOOKUP["metric_names"].get(metric, None)
        if metric_name is None:
            metric_name = " ".join([x.capitalize() for x in metric.strip().split(" ")])
        names.append(metric_name)
    return names


# ===============APP LAYOUT====================#
app.layout = html.Div(
    id="app-body-container",
    children=[
        html.Div(
            [
                # global filters (affect entire dashboard)
                dbc.Row(
                    [
                        html.Span("Analytics Dashboard", className="dashboard-title"),
                        html.Div(
                            className="dashboard-comp-container",
                            children=[
                                html.P("Time Frame", className="input-label"),
                                dcc.Dropdown(
                                    id="timeframe",
                                    options=[
                                        {"label": o, "value": o.lower()}
                                        for o in [
                                            "1 Day ",
                                            "1 Week",
                                            "1 Month",
                                            "1 Year",
                                            "All",
                                        ]
                                    ],
                                    value="1 year",
                                    style={
                                        "margin-top": "5px",
                                        "margin-bottom": "5px",
                                        "width": "120px",
                                    },
                                    searchable=False,
                                    clearable=False,
                                ),
                            ],
                            style={
                                "display": "flex",
                                "margin-right": "10px",
                                "margin-left": "10px",
                            },
                        ),
                    ],
                    style={"margin-left": "0px"},
                ),
                html.Div(
                    [
                        dbc.Col(
                            [
                                dbc.Row(
                                    [
                                        html.Div(
                                            id="callout-container",
                                            style={
                                                "display": "flex",
                                                "text-align": "center",
                                            },
                                        )
                                        
                                       
                                    ],
                                    style={"margin-left": "0px"},
                                ),
                                dbc.Row(
                                    [
                                        html.Div(
                                            className="dashboard-comp-container",
                                            children=[
                                                html.P(
                                                    "Map Metric",
                                                    className="input-label",
                                                ),
                                                dcc.Dropdown(
                                                    id="map_metric",
                                                    options=[
                                                        {
                                                            "label": LOOKUP[
                                                                "metric_names"
                                                            ][o],
                                                            "value": o,
                                                        }
                                                        for o in get_metrics()
                                                    ],
                                                    value="Total Deaths",
                                                    style={
                                                        "margin-top": "5px",
                                                        "margin-bottom": "5px",
                                                        "width": "200px",
                                                    },
                                                    searchable=False,
                                                    clearable=False,
                                                ),
                                            ],
                                            style={"display": "flex"},
                                        ),
                                        html.Div(
                                            [
                                                html.P(
                                                    "Granularity",
                                                    className="input-label",
                                                ),
                                                dcc.Dropdown(
                                                    id="granularity",
                                                    options=[
                                                        {"label": o, "value": o}
                                                        for o in [
                                                            "District",
                                                            "Province",
                                                        ]
                                                    ],
                                                    value="District",
                                                    style={
                                                        "margin-top": "5px",
                                                        "margin-bottom": "5px",
                                                        "width": "120px",
                                                    },
                                                    searchable=False,
                                                    clearable=False,
                                                ),
                                            ],
                                            className="dashboard-comp-container",
                                        ),
                                    ],
                                    style={"align-items": "center"},
                                ),
                                # map container
                                dcc.Loading(id='map-loader',
                                    type='circle',
                                    children=[
                                    html.Div(
                                        id="choropleth-container",
                                        children=dcc.Graph(id="choropleth"),
                                    )
                                        
                                ]),
                                html.Div(id="va_data", style={"display": "none"}),
                                html.Div(id="filter_dict", style={"display": "none"}),
                            ],
                            width=7,
                        ),
                        dbc.Col(
                            [
                                dcc.Tabs(
                                    [  # graph tabs
                                        dcc.Tab(
                                            label="COD Analysis",
                                            children=[  # tab 1: COD Analysis
                                                html.Div(
                                                    id="cod_buttons",
                                                    children=[
                                                        html.Div(
                                                            [
                                                                html.P(
                                                                    "Demographic",
                                                                    className="input-label",
                                                                ),
                                                                dcc.Dropdown(
                                                                    id="cod_factor",
                                                                    options=[
                                                                        {
                                                                            "label": o,
                                                                            "value": o,
                                                                        }
                                                                        for o in [
                                                                            "All",
                                                                            "Age Group",
                                                                            "Sex",
                                                                        ]
                                                                    ],
                                                                    value="All",
                                                                    style={
                                                                        "margin-top": "5px",
                                                                        "margin-bottom": "5px",
                                                                        "width": "120px",
                                                                    },
                                                                    searchable=False,
                                                                    clearable=False,
                                                                ),
                                                            ],
                                                            style={
                                                                "display": "flex",
                                                                "margin-right": "30px",
                                                            },
                                                        ),
                                                        html.Div(
                                                            [
                                                                html.P(
                                                                    "N",
                                                                    className="input-label",
                                                                ),
                                                                dcc.Dropdown(
                                                                    id="cod_n",
                                                                    options=[
                                                                        {
                                                                            "label": o,
                                                                            "value": o,
                                                                        }
                                                                        for o in [
                                                                            5,
                                                                            10,
                                                                            15,
                                                                            20,
                                                                        ]
                                                                    ],
                                                                    value=10,
                                                                    style={
                                                                        "margin-top": "5px",
                                                                        "margin-bottom": "5px",
                                                                        "width": "60px",
                                                                    },
                                                                    searchable=False,
                                                                    clearable=False,
                                                                ),
                                                            ],
                                                            style={"display": "flex"},
                                                        ),
                                                        dbc.RadioItems(
                                                            id="cod-aggtype",
                                                            options=[
                                                                {
                                                                    "label": "% of Total",
                                                                    "value": "percent_total",
                                                                },
                                                                {
                                                                    "label": "Counts",
                                                                    "value": "counts",
                                                                },
                                                            ],
                                                            value="cts",
                                                            labelStyle={
                                                                "display": "inline-block"
                                                            },
                                                            labelClassName="radio-group-labels",
                                                            labelCheckedClassName="radio-group-labels-checked",
                                                            style={
                                                                "margin-left": "30px",
                                                                "display": "flex",
                                                            },
                                                        ),
                                                    ],
                                                    style={
                                                        "display": "flex",
                                                        "align-items": "center",
                                                    },
                                                ),
                                                dcc.Loading(html.Div(id="cod-container"), type='circle'),
                                            ],
                                        ),
                                        dcc.Tab(
                                            label="Age Distribution",
                                            children=[dcc.Loading(html.Div(id="age-container"), type='circle')]
                                        ),
                                        dcc.Tab(
                                            label="Gender Distribution",
                                            children=[dcc.Loading(html.Div(id="sex-container"))]
                                        ),
                                        dcc.Tab(
                                            label="Place of Death Distribution",
                                            children=[dcc.Loading(html.Div(id="pod-container"))]
                                        ),
                                        dcc.Tab(
                                            label="VA Trends",
                                            children=[
                                                html.Div(
                                                    id="ts_buttons",
                                                    children=[
                                                        html.Div(
                                                            [
                                                                html.P(
                                                                    "Aggregation",
                                                                    className="input-label",
                                                                ),
                                                                dcc.Dropdown(
                                                                    id="group_period",
                                                                    options=[
                                                                        {
                                                                            "label": o,
                                                                            "value": o,
                                                                        }
                                                                        for o in [
                                                                            "Day",
                                                                            "Week",
                                                                            "Month",
                                                                            "Year",
                                                                        ]
                                                                    ],
                                                                    value="Month",
                                                                    style={
                                                                        "margin-top": "5px",
                                                                        "margin-bottom": "5px",
                                                                        "width": "120px",
                                                                        "margin-right": "30px",
                                                                    },
                                                                    searchable=False,
                                                                    clearable=False,
                                                                ),
                                                                html.P(
                                                                    "Demographic",
                                                                    className="input-label",
                                                                ),
                                                                dcc.Dropdown(
                                                                    id="ts_factor",
                                                                    options=[
                                                                        {
                                                                            "label": o,
                                                                            "value": o,
                                                                        }
                                                                        for o in [
                                                                            "All",
                                                                            "Age Group",
                                                                            "Sex",
                                                                            "Place of Death",
                                                                        ]
                                                                    ],
                                                                    value="All",
                                                                    style={
                                                                        "margin-top": "5px",
                                                                        "margin-bottom": "5px",
                                                                        "width": "140px",
                                                                    },
                                                                    searchable=False,
                                                                    clearable=False,
                                                                ),
                                                            ],
                                                            style={
                                                                "display": "flex",
                                                                "margin-right": "30px",
                                                            },
                                                        ),
                                                        dcc.Loading(html.Div(id="ts-container"), type='circle'),
                                                    ],
                                                )
                                            ],
                                        ),
                                    ]
                                )
                            ]
                        ),
                    ],
                    style={"display": "flex", "margin-top": "10px"},
                ),
            ]
        )
    ],
)

# ============ VA data (loaded from database and shared across components) ========

@app.callback(
    Output(component_id="va_data", component_property="children"),
    [
        Input(component_id="timeframe", component_property="value"),
    ],
)
def va_data(timeframe="All"):
    data = load_va_data()
    return data.to_json()


# ============ Filter logic (update filter table used by other componenets)========#
@app.callback(
    Output(component_id="filter_dict", component_property="children"),
    [
        Input(component_id="va_data", component_property="children"),
        Input(component_id="choropleth", component_property="selectedData"),
        Input(component_id="granularity", component_property="value"),
        Input(component_id="timeframe", component_property="value"),
    ],
)
def filter_data(
    va_data, selected_json, granularity=INITIAL_GRANULARITY, timeframe="All", search_terms=[]
):
    filter_df = pd.read_json(va_data)
    granularity = granularity.lower()

    # first, check for locations clicked on map.
    if selected_json is not None:
        point_df = pd.DataFrame(selected_json["points"])
        chosen_region_coordinates = set(point_df["location"].tolist())
        filter_col = granularity.lower()
        filter_df = filter_df[filter_df[filter_col].isin(chosen_region_coordinates)]

    # next, apply time filter if necessary
    if timeframe != "all":
        cutoff = dt.datetime.today() - dt.timedelta(
            days=LOOKUP["time_dict"][timeframe]
        )
        filter_df = filter_df[filter_df["date"] >= cutoff]

    filter_ids = filter_df.index.tolist()
    filter_dict = {"geo_filter": (selected_json is not None), "ids": filter_ids}

    return json.dumps(filter_dict)


# ====================Map Logic===================================#
@app.callback(
    Output(component_id="choropleth-container", component_property="children"),
    [
        Input(component_id="va_data", component_property="children"),
        Input(component_id="timeframe", component_property="value"),
        Input(component_id="granularity", component_property="value"),
        Input(component_id="map_metric", component_property="value"),
        Input(component_id="filter_dict", component_property="children"),
    ],
)
def update_choropleth(
    va_data, timeframe, granularity, map_metric="Total Deaths", filter_dict=None, geojson=GEOJSON
):
    plot_data = pd.read_json(va_data)
    return_value = html.Div(id="choropleth")
    if plot_data.size > 0:
        granularity = granularity.lower()
        timeframe = timeframe.lower()
        feature_id = "properties.area_name"
        chosen_region_coordinates = geojson["features"]
        # if dashboard filter applied, carry over to data
        if filter_dict is not None:
            filter_dict = json.loads(filter_dict)
            plot_data = plot_data.iloc[filter_dict["ids"], :]
            # if user has clicked on map and granularity is providence level, change to district  level
            if filter_dict["geo_filter"] and granularity == "province":
                granularity = "district"
            chosen_regions = set(plot_data[granularity].tolist())
            chosen_region_coordinates = [
                g
                for g in geojson["features"]
                if g["properties"]["area_name"] in chosen_regions
            ]

        if map_metric not in ["Total Deaths", "Mean Age of Death"]:
            plot_data = plot_data[plot_data["cause"] == map_metric]

        # get map tooltips
        map_df = generate_map_data(plot_data, geojson, granularity)

        data_value = "mean" if len(re.findall("[mM]ean", map_metric)) > 0 else "count"
        figure = go.Figure(
            data=go.Choropleth(
                locations=map_df[granularity],
                z=map_df[data_value].astype(float),
                locationmode="geojson-id",
                geojson=geojson,
                featureidkey=feature_id,
                colorscale="Blues",
                hovertext=map_df["tooltip"],
                hoverinfo="text",
                autocolorscale=False,
                marker_line_color="black",  # line markers between states
                marker_line_width=0.25,
                colorbar=dict(
                    title="{} by {}".format(
                        map_metric.capitalize(), granularity.capitalize()
                    ),
                    thicknessmode="fraction",
                    thickness=0.03,
                    lenmode="fraction",
                    len=0.8,
                    yanchor="middle",
                    ticks="outside",
                    dtick=5,
                ),
            )
        )

        # update figure layout
        figure.update_layout(
            margin={"r": 0, "t": 0, "l": 0, "b": 0},
            clickmode="event+select",
            dragmode="select",
        )
        # additional styling
        config = {"displayModeBar": True}
        figure.update_geos(
            fitbounds="locations",
            visible=True,
            showcountries=True,
            showlakes=False,
            countrycolor="lightgray",
            showsubunits=True,
            landcolor="rgb(250,250,248)",
            framewidth=0,
        )

        # adjust automatic zoom to maximize size of map
        xmin = min([g["properties"]["min_x"] for g in chosen_region_coordinates])
        xmax = max([g["properties"]["max_x"] for g in chosen_region_coordinates])
        ymin = min([g["properties"]["min_y"] for g in chosen_region_coordinates])
        ymax = max([g["properties"]["max_y"] for g in chosen_region_coordinates])

        xmin, xmax, ymin, ymax = 0.95 * xmin, 1.05 * xmax, 1.05 * ymin, 0.95 * ymax
        figure.update_geos(lonaxis_range=[xmin, xmax], lataxis_range=[ymin, ymax])
        return_value = dcc.Graph(id="choropleth", figure=figure, config=config)        

    return return_value


# ==========Map dataframe (built from va dataframe)============#
def generate_map_data(va_df, geojson, granularity="district"):
    if va_df.size > 0:
        map_df = (
            va_df[[granularity, "age", "location"]]
            .groupby(granularity)
            .agg({"age": ["mean", "count"], "location": [pd.Series.nunique]})
        )
        map_df[granularity] = map_df.index.values
        # remove unnecessary index (colapse multiindex down to single index)
        for old_index in map_df.columns.levels[0]:
            if len(map_df[old_index].shape) == 2:
                for col in map_df[old_index].columns:
                    map_df[col] = map_df[old_index][col]

        map_df["mean"] = np.round(map_df["mean"], 1)
        df = map_df
        df["tooltip"] = (
            "<b>"
            + granularity.capitalize()
            + ": </b>"
            + df[granularity]
            + "<br>"
            + "<b>Total Deaths: </b>"
            + df["count"].astype(str)
            + "<br>"
            + "<b>Average Lifespan: </b>"
            + df["mean"].astype(str)
            + "<br>"
            + "<b>Active Facilities: </b>"
            + df["nunique"].astype(str)
        )
        return df
    return pd.DataFrame()


# TODO: Get this filter to work properly
# @app.callback(
#
#       [Output(component_id='map_metric', component_property='options')],
#       [Input(component_id='filter_dict', component_property='children')]
# )
#
# def update_dropdown(filter_dict=None):
#    plot_data = va_data()
#    if filter_dict is not None:
#        plot_data = plot_data.iloc[json.loads(filter_dict)['ids'],:]
#    relevant_metrics = get_metrics(plot_data)
#    options=[{'label': LOOKUP['metric_names'][o], 'value': o} for o in relevant_metrics]
#    return options


# =========Callout Boxes Logic============================================#
@app.callback(
    Output(component_id="callout-container", component_property="children"),
    [
        Input(component_id="va_data", component_property="children"),
        Input(component_id="timeframe", component_property="value"),
        Input(component_id="granularity", component_property="value"),
        Input(component_id="filter_dict", component_property="children"),
    ],
)
def update_callouts(va_data, timeframe, granularity, filter_dict=None):
    plot_data = pd.read_json(va_data)
    if plot_data.size > 0:
        if filter_dict is not None:
            plot_data = plot_data.iloc[json.loads(filter_dict)["ids"], :]

        granularity = granularity.lower()

        # tot VAs
        total_vas = plot_data.shape[0]

        # active facilities
        active_facilities = plot_data["location"].nunique()

        # TODO: get field worker data from ODK - this is just a janky hack
        num_field_workers = int(1.25 * active_facilities)

        # region coverage
        total_regions = plot_data[granularity].nunique()
        regions_covered = (
            plot_data[[granularity, "age"]].dropna()[granularity].nunique()
        )
        coverage = "{}%".format(np.round(100 * regions_covered / total_regions, 0))

        return [
            make_card(total_vas, header="Total VAs"),
            make_card(active_facilities, header="Active Facilities"),
            make_card(num_field_workers, header="Field Workers"),
            make_card(coverage, header="Region Coverage"),
        ]
    else:
        return [[html.Div() for i in range(4)]]


# build a calloutbox with specific value
# colors: primary, secondary, info, success, warning, danger, light, dark
def make_card(
    value, header=None, description="", color="light", inverse=False, style=None
):
    card_content = []
    if header is not None:
        card_content.append(dbc.CardHeader(header))
    body = dbc.CardBody(
        [
            html.H3(value, className="card-title"),
            html.P(description, className="card-text",),
        ],
        style={"padding": ".5rem"},
    )
    card_content.append(body)
    if style is None:
        style = {"width": "190px"}
    card_obj = dbc.Card(card_content, color=color, inverse=inverse, className="mr-2")
    card_container = html.Div(card_obj, style=style)
    return card_container


# =========Cause of Death Plot Logic============================================#
@app.callback(
    Output(component_id="cod-container", component_property="children"),
    [
        Input(component_id="va_data", component_property="children"),
        Input(component_id="timeframe", component_property="value"),
        Input(component_id="cod_factor", component_property="value"),
        Input(component_id="cod_n", component_property="value"),
        Input(component_id="cod-aggtype", component_property="value"),
        Input(component_id="filter_dict", component_property="children"),
    ],
)
def cod_plot(va_data, timeframe, factor="All", N=10, agg_type="counts", filter_dict=None):
    figure = go.Figure()
    plot_data = pd.read_json(va_data)
    if plot_data.size > 0:
        if filter_dict is not None:
            plot_data = plot_data.iloc[json.loads(filter_dict)["ids"], :]

        factor = factor.lower()
        if factor != "all":
            assert factor in ["age group", "sex"]
            factor_col = LOOKUP["demo_to_col"][factor]
            factor_title = "by " + factor.capitalize()
            counts = plot_data.pivot_table(
                index="cause",
                columns=factor_col,
                values="id",
                aggfunc=pd.Series.nunique,
                fill_value=0,
                margins=True,
            )
            plot_fn = go.Scatter
        else:
            counts = pd.DataFrame({"All": plot_data.cause.value_counts()})
            factor_title = "Overall"
            plot_fn = go.Bar
        counts["cod"] = counts.index
        counts = counts[counts["cod"] != "All"]
        counts = counts.sort_values(by="All", ascending=False).head(N)
        groups = list(set(counts.columns).difference(set(["cod"])))
        if factor != "all":
            groups.remove("All")
        for i, group in enumerate(groups):
            if agg_type != "counts":
                counts[group] = 100 * counts[group] / counts[group].sum()
            figure.add_trace(
                plot_fn(
                    y=counts[group],
                    x=counts["cod"],
                    name=group.capitalize(),
                    orientation="v",
                    marker=dict(
                        color=LOOKUP["color_list"][i],
                        line=dict(color="rgb(158,158,158)", width=1),
                    ),
                )
            )
        figure.update_layout(
            barmode="stack",
            title_text="Top {} Causes of Death {}".format(N, factor_title),
            xaxis_tickangle=-45,
            yaxis_title="Count" if agg_type == "counts" else "Percent",
        )

    return dcc.Graph(id="cod_plot", figure=figure)


# =========Age Distribution Plot Logic============================================#
@app.callback(
    Output(component_id="age-container", component_property="children"),
    [
        Input(component_id="va_data", component_property="children"),
        Input(component_id="timeframe", component_property="value"),
        Input(component_id="filter_dict", component_property="children"),
    ],
)
def age_plot(va_data, timeframe, filter_dict=None, bins=9):
    figure = go.Figure()
    plot_data = pd.read_json(va_data)
    if plot_data.size > 0:
        if filter_dict is not None:
            plot_data = plot_data.iloc[json.loads(filter_dict)["ids"], :]

        historgram_data = [plot_data["age"].dropna().tolist()]
        group_labels = ["Verbal Autopsies"]  # name of the dataset

        figure = ff.create_distplot(
            historgram_data, group_labels, show_rug=False, bin_size=[bins]
        )
        figure.update_layout(
            title_text="Verbal Autopsy Age Distribution",
            xaxis_title="Age",
            yaxis_title="Density",
        )

    return dcc.Graph(id="age_plot", figure=figure)


# =========Gender Plot Logic============================================#
@app.callback(
    Output(component_id="sex-container", component_property="children"),
    [
        Input(component_id="va_data", component_property="children"),
        Input(component_id="timeframe", component_property="value"),
        Input(component_id="filter_dict", component_property="children"),
    ],
)
def sex_plot(va_data, timeframe, filter_dict=None):
    figure = go.Figure()
    plot_data = pd.read_json(va_data)
    if plot_data.size > 0:
        if filter_dict is not None:
            plot_data = plot_data.iloc[json.loads(filter_dict)["ids"], :]
        column_name = LOOKUP["demo_to_col"]["sex"]
        sex_counts = plot_data[column_name].value_counts()
        figure.add_trace(
            go.Pie(labels=sex_counts.index.tolist(), values=sex_counts.values, hole=0.3)
        )
        figure.update_layout(title_text="Verbal Autopsies by Gender")
    return dcc.Graph(id="sex_plot", figure=figure)


# ========= Time Series Plot Logic============================================#
@app.callback(
    Output(component_id="ts-container", component_property="children"),
    [
        Input(component_id="va_data", component_property="children"),
        Input(component_id="timeframe", component_property="value"),
        Input(component_id="group_period", component_property="value"),
        Input(component_id="filter_dict", component_property="children"),
        Input(component_id="ts_factor", component_property="value"),
    ],
)
def trend_plot(va_data, timeframe, group_period, filter_dict=None, factor="All"):
    figure = go.Figure()
    plot_data = pd.read_json(va_data)
    if plot_data.size > 0:
        if filter_dict is not None:
            plot_data = plot_data.iloc[json.loads(filter_dict)["ids"], :]

        group_period = group_period.lower()
        aggregate_title = group_period.capitalize()
        plot_data["date"] = pd.to_datetime(plot_data["date"])
        plot_data["timegroup"] = pd.to_datetime(plot_data["date"])
        if group_period == "week":
            plot_data["timegroup"] = pd.to_datetime(
                plot_data["date"]
                .dt.to_period("W")
                .apply(lambda x: x.strftime("%Y-%m-%d"))
            )
        elif group_period == "month":
            plot_data["timegroup"] = pd.to_datetime(
                plot_data["date"].dt.to_period("M").apply(lambda x: x.strftime("%Y-%m"))
            )
        elif group_period == "year":
            plot_data["timegroup"] = plot_data["date"].dt.to_period("Y").astype(str)

        dtype = "category" if group_period == "year" else "date"

        factor = factor.lower()
        if factor != "all":
            assert factor in LOOKUP["demo_to_col"]
            factor_col = LOOKUP["demo_to_col"][factor]
            trend_counts = plot_data.pivot_table(
                index="timegroup",
                columns=factor_col,
                values="id",
                aggfunc=pd.Series.nunique,
                fill_value=0,
                margins=False,
            )
            plot_fn = go.Scatter
        else:
            trend_counts = (
                plot_data[["timegroup", "id"]]
                .groupby("timegroup")
                .count()
                .rename(columns={"id": "all"})
            )
            plot_fn = go.Bar

        for i, group in enumerate(trend_counts.columns.tolist()):
            figure.add_trace(
                plot_fn(
                    y=trend_counts[group],
                    x=trend_counts.index,
                    name=group.capitalize(),
                    marker=dict(
                        color=LOOKUP["color_list"][i],
                        line=dict(color=LOOKUP["color_list"][i], width=1),
                    ),
                )
            )
        figure.update_layout(
            title_text="Verbal Autopsies by {}".format(aggregate_title),
            xaxis_title=aggregate_title,
            yaxis_title="Verbal Autopsy Count",
            xaxis_type=dtype,
            xaxis_tickangle=-45,
            xaxis_tickformatstops=[
                dict(
                    dtickrange=[None, None],
                    value=LOOKUP["date_display_formats"].get(group_period, "%d/%m/%Y"),
                )
            ],
        )
    return dcc.Graph(id="trend_plot", figure=figure)


# =========Place of Death Plot Logic============================================#
@app.callback(
    Output(component_id="pod-container", component_property="children"),
    [
        Input(component_id="va_data", component_property="children"),
        Input(component_id="filter_dict", component_property="children")
    ],
)
def place_of_death_plt(va_data, filter_dict=None):
    figure = go.Figure()
    plot_data = pd.read_json(va_data)
    if plot_data.size > 0:
        if filter_dict is not None:
            plot_data = plot_data.iloc[json.loads(filter_dict)["ids"], :]
        plot_data["Id10058"] = plot_data["Id10058"].apply(
            lambda x: LOOKUP["death_location_names"].get(x, x.capitalize())
        )
        location_counts = plot_data["Id10058"].value_counts()
        figure = go.Figure(
            go.Pie(
                labels=location_counts.index.tolist(),
                values=location_counts.values,
                hole=0.3,
            )
        )
        figure.update_layout(title_text="VAs by Place of Death")
    return dcc.Graph(id="pod_plt", figure=figure)


# uncomment this if running as Dash app (as opposed to DjangoDash app)
# app.run_server(debug= True)
