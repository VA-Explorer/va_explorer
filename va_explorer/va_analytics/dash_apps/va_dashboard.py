#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jul 29 15:25:20 2020

@author: babraham
"""

import datetime as dt
import json
import os
import re

import dash
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
import numpy as np
import pandas as pd
import plotly.graph_objs as go
from dash.dependencies import Input, Output
from django_plotly_dash import DjangoDash

import va_explorer.utils.plotting as plotting
from va_explorer.va_data_management.models import Location, VerbalAutopsy

# ================APP DEFINITION===============#
# NOTE: to include external stylesheets, set external_stylesheets parameter in constructor
# app = dash.Dash(__name__)  # Dash constructor
app = DjangoDash(name="va_dashboard", serve_locally=True, add_bootstrap_links=True)

# Toolbar configurations
graph_config = {"displayModeBar": True, "scrollZoom": True, "displaylogo": False, "modeBarButtonsToRemove":["zoomInGeo", "zoomOutGeo", "select2d", "lasso2d"]}
chart_config = {"displayModeBar": True, "displaylogo":False, "modeBarButtonsToRemove":["pan2d", "zoom2d", "select2d", "lasso2d", "zoomIn2d", "zoomOut2d", "autoScale2d", "resetScale2d"]}

# TODO: We should eventually move this mapping to someplace where it's more configurable
# ===========INITIAL CONFIG VARIABLES=============#
# initial timeframe for map data to display
INITIAL_TIMEFRAME = "all"
# folder where geojson is kept
JSON_DIR = "va_explorer/va_analytics/dash_apps/geojson"
# Zambia Geojson pulled from: https://adr.unaids.org/dataset/zambia-geographic-data-2019
JSON_FILE = "zambia_geojson.json"
# initial granularity
INITIAL_GRANULARITY = "district"
# initial metric to plot on map
INITIAL_COD_TYPE = "all"
# ============Lookup dictionaries =================#


LOOKUP = plotting.load_lookup_dicts()


# =============Geo dictionaries and global variables ========#
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


GEOJSON = load_geojson_data(json_file=f"{JSON_DIR}/{JSON_FILE}")


# ============ VA Data =================
def load_va_data(geographic_levels=None):
    np.random.seed(23)
    return_dict = {"data": {"valid": pd.DataFrame(), "invalid": pd.DataFrame()}}

    all_vas = VerbalAutopsy.objects.prefetch_related("location").prefetch_related(
        "causes"
    )

    if len(all_vas) > 0:
        # Grab exactly the fields we need, including location and cause data
        va_data = [
            {
                "id": va.id,
                "Id10019": va.Id10019,
                "Id10058": va.Id10058,
                "ageInYears": va.ageInYears,
                "location": va.location.name,
                "cause": get_va_cause(va),
            }
            for va in all_vas
        ]

        # Build a location ancestors lookup and add location information at all levels to all vas
        # TODO: This is not efficient (though it's better than 2 DB queries per VA)
        # TODO: This assumes that all VAs will occur in a facility, ok?
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

        # clean up age fields and assign to age bin
        va_df["age"] = va_df["ageInYears"].replace(
            to_replace=["dk"], value=np.random.randint(1, 80)
        )
        va_df["age"] = pd.to_numeric(va_df["age"], errors="coerce")
        va_df["age_group"] = va_df["age"].apply(assign_age_group)
        cur_date = dt.datetime.today()

        # TODO: This random date of death assignment needs to be correctly handled
        # NOTE: date field called -Id10023 in VA form, but no dates in curent responses
        va_df["date"] = [
            cur_date - dt.timedelta(days=int(x))
            for x in np.random.randint(3, 400, size=va_df.shape[0])
        ]

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


def get_va_cause(va_obj):
    causes = va_obj.causes.all()
    if len(causes) > 0:
        return causes[0].cause

    return None


def assign_age_group(age):
    if age <= 1:
        return "neonate"
    if age <= 16:
        return "child"
    # default
    return "adult"


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
                                html.P("Time Period", className="input-label"),
                                dcc.Dropdown(
                                    id="timeframe",
                                    options=[
                                        {"label": o, "value": o.lower()}
                                        for o in [
                                            "Today",
                                            "Last Week",
                                            "Last Month",
                                            "Last 6 Months",
                                            "Last Year",
                                            "All",
                                        ]
                                    ],
                                    value=INITIAL_TIMEFRAME,
                                    style={
                                        "margin-top": "5px",
                                        "margin-bottom": "5px",
                                        "width": "140px",
                                    },
                                    searchable=False,
                                    clearable=False,
                                    disabled=False,
                                ),
                            ],
                        ),
                        html.Div(
                            className="dashboard-comp-container",
                            children=[
                                html.P("Cause of Death", className="input-label",),
                                dcc.Dropdown(
                                    id="cod_type",
                                    value=INITIAL_COD_TYPE,
                                    options=[{"label": "All Causes", "value": "all"}],
                                    style={
                                        "margin-top": "5px",
                                        "margin-bottom": "5px",
                                        "width": "200px",
                                    },
                                    searchable=True,
                                    clearable=False,
                                ),
                            ],
                        ),
                        html.Div(
                            className="dashboard-comp-container",
                            children=[
                                html.P(
                                    "View", id="view_label", className="input-label",
                                ),
                                dcc.Dropdown(
                                    id="view_level",
                                    value="",
                                    placeholder="Auto",
                                    style={
                                        "margin-top": "5px",
                                        "margin-bottom": "5px",
                                        "width": "100px",
                                    },
                                    searchable=False,
                                    clearable=False,
                                    disabled=False,
                                ),
                            ],
                        ),
                        html.Div(
                            id="button-container",
                            children=[
                                html.Div(
                                    id="reset_container",
                                    className="dashboard-comp-container",
                                    children=[
                                        dbc.Button(
                                            "Reset",
                                            id="reset",
                                            color="secondary",
                                            className="mr-1",
                                            n_clicks=0,
                                        )
                                    ],
                                ),
                                html.Div(
                                    id="download_container",
                                    className="dashboard-comp-container",
                                    children=[
                                        html.A(
                                            dbc.Button(
                                                "Download Data", color="primary"
                                            ),
                                            href="/va_analytics/download",
                                        )
                                    ],
                                ),
                            ],
                            style={
                                "align-items": "flex-end",
                                "display": "flex",
                                "margin-bottom": "10px",
                            },
                        ),
                    ],
                    style={"padding-bottom": "10px"},
                ),
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                dbc.Row(
                                    [
                                        html.Div(
                                            id="callout-container",
                                            style={
                                                "display": "contents",
                                                "text-align": "center",
                                            },
                                        )
                                    ],
                                    style={"margin-left": "0px"},
                                ),
                                dbc.Row(
                                    [
                                        html.Span(
                                            className="fas fa-search",
                                            style={"margin-top": "10px"},
                                        ),
                                        html.Div(
                                            className="dashborad-comp-container",
                                            id="search-container",
                                            children=[
                                                dcc.Dropdown(
                                                    id="map_search",
                                                    options=[],
                                                    multi=False,
                                                    placeholder="Search Locations (or click on map)",
                                                    clearable=True,
                                                )
                                            ],
                                            style={
                                                "margin-left": "10px",
                                                "width": "90%",
                                            },
                                        ),
                                    ],
                                    style={
                                        "padding-left": "20px",
                                        "padding-right": "15px",
                                        "margin-top": "15px",
                                        "padding-bottom": "10px",
                                    },
                                ),
                                dbc.Row([], style={"align-items": "center"},),
                                # map container
                                dcc.Loading(
                                    id="map-loader",
                                    type="circle",
                                    children=[
                                        html.Div(
                                            id="choropleth-container",
                                            children=dcc.Graph(id="choropleth", config=graph_config),
                                        )
                                    ],
                                ),
                                html.Div(id="bounds"),
                                html.Div(id="va_data", style={"display": "none"}),
                                html.Div(
                                    id="invalid_va_data", style={"display": "none"}
                                ),
                                html.Div(id="locations", style={"display": "none"}),
                                html.Div(
                                    id="location_types", style={"display": "none"}
                                ),
                                html.Div(id="filter_dict", style={"display": "none"}),
                            ],
                            width=8,
                            style={"min-width": "480px", "margin-bottom": "15px"},
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
                                                        dbc.Row(
                                                            [
                                                                dbc.Col(
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
                                                                        "display": "flex"
                                                                    },
                                                                    width=6,
                                                                ),
                                                                dbc.Col(
                                                                    [
                                                                        dcc.Dropdown(
                                                                            id="cod_n",
                                                                            options=[
                                                                                {
                                                                                    "label": f"Top {o}",
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
                                                                            },
                                                                            searchable=False,
                                                                            clearable=False,
                                                                        )
                                                                    ],
                                                                    width=3,
                                                                    style={
                                                                        "margin-top": "5px"
                                                                    },
                                                                ),
                                                                # TODO: add COD groupings dropdown
                                                                dbc.Col([], width=3),
                                                            ],
                                                        ),
                                                        dcc.Loading(
                                                            html.Div(
                                                                id="cod-container"
                                                            ),
                                                            type="circle",
                                                        ),
                                                    ],
                                                )
                                            ],
                                        ),
                                        dcc.Tab(
                                            label="Demographics",
                                            children=[
                                                dcc.Loading(
                                                    html.Div(id="demos-container"),
                                                    type="circle",
                                                )
                                            ],
                                        ),
                                        dcc.Tab(
                                            label="VA Trends",
                                            children=[
                                                html.Div(
                                                    id="ts_buttons",
                                                    children=[
                                                        dbc.Row(
                                                            [
                                                                dbc.Col(
                                                                    [
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
                                                                        "display": "flex"
                                                                    },
                                                                    width=6,
                                                                ),
                                                                dbc.Col(
                                                                    [
                                                                        dcc.Dropdown(
                                                                            id="group_period",
                                                                            options=[
                                                                                {
                                                                                    "label": f"By {o}",
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
                                                                            },
                                                                            searchable=False,
                                                                            clearable=False,
                                                                        ),
                                                                    ],
                                                                    style={
                                                                        "display": "flex",
                                                                    },
                                                                    width=4,
                                                                ),
                                                            ],
                                                        ),
                                                        dcc.Loading(
                                                            html.Div(id="ts-container"),
                                                            type="circle",
                                                        ),
                                                    ],
                                                )
                                            ],
                                        ),
                                    ]
                                )
                            ],
                            width=4,
                            style={"min-width": "480px", "margin-bottom": "15px"},
                        ),
                    ],
                ),
            ]
        )
    ],
)


# =============Reset logic (reset map to default)====================#
@app.callback(
    [
        Output(component_id="map_search", component_property="value"),
        Output(component_id="cod_type", component_property="value"),
    ],
    [Input(component_id="reset", component_property="n_clicks")],
)
def reset(n_clicks=0):
    return "", INITIAL_COD_TYPE


# ============ VA data (loaded from database and shared across components) ========
@app.callback(
    [
        Output(component_id="va_data", component_property="children"),
        Output(component_id="invalid_va_data", component_property="children"),
        Output(component_id="locations", component_property="children"),
        Output(component_id="location_types", component_property="children"),
    ],
    [Input(component_id="timeframe", component_property="value"),],
)
def init_va_data(timeframe="All"):
    res = load_va_data()
    valid_va_data = res["data"]["valid"].to_json()
    invalid_va_data = res["data"]["invalid"].to_json()
    locations = json.dumps(res.get("locations", []))
    location_types = json.dumps(res.get("location_types", []))
    return valid_va_data, invalid_va_data, locations, location_types


# ============ Location search options (loaded after load_va_data())==================
@app.callback(
    Output(component_id="map_search", component_property="options"),
    [
        Input(component_id="map_search", component_property="search_value"),
        Input(component_id="locations", component_property="children"),
    ],
)
def update_options(search_value, location_json):
    if search_value and location_json:
        locations = json.loads(location_json).keys()
        options = [
            {"label": location, "value": location}
            for location in locations
            if search_value.lower() in location.lower()
        ]
        return options

    raise dash.exceptions.PreventUpdate


# ============ Filter logic (update filter table used by other componenets)========#
@app.callback(
    [
        Output(component_id="filter_dict", component_property="children"),
        Output(component_id="timeframe", component_property="disabled"),
    ],
    [
        Input(component_id="va_data", component_property="children"),
        Input(component_id="invalid_va_data", component_property="children"),
        Input(component_id="choropleth", component_property="selectedData"),
        Input(component_id="timeframe", component_property="value"),
        Input(component_id="cod_type", component_property="value"),
        Input(component_id="map_search", component_property="value"),
        Input(component_id="locations", component_property="children"),
        Input(component_id="location_types", component_property="children"),
    ],
)
def filter_data(
    va_data,
    invalid_va_data,
    selected_json,
    timeframe="all",
    cod_type="all",
    search_terms=[],
    locations=None,
    location_types=None,
):
    if va_data is not None:
        valid_va_df = pd.read_json(va_data)
        invalid_va_df = pd.read_json(invalid_va_data)
        locations = json.loads(locations) if isinstance(locations, str) else locations
        search_terms = [] if search_terms is None else search_terms
        location_types = (
            json.loads(location_types) if location_types is not None else location_types
        )
        disable_timeframe = False

        # filter valid vas (VAs with COD)
        valid_filter = _get_filter_dict(
            valid_va_df,
            selected_json,
            timeframe=timeframe,
            location_types=location_types,
            search_terms=search_terms,
            locations=locations,
        )
        # filter invalid vas (VAs without COD)
        invalid_filter = _get_filter_dict(
            invalid_va_df,
            selected_json,
            timeframe=timeframe,
            location_types=location_types,
            search_terms=search_terms,
            locations=locations,
        )
        # combine filters into one dictionary to share across callbacks
        combined_filter_dict = {
            "granularity": valid_filter["granularity"],  # same across both dictionaries
            "plot_regions": valid_filter[
                "plot_regions"
            ],  # same across both dictionaries
            "geo_filter": valid_filter["geo_filter"],  # same across both dictionaries
            "chosen_region": valid_filter[
                "chosen_region"
            ],  # same across both dictionaries
            "ids": {"valid": valid_filter["ids"], "invalid": invalid_filter["ids"]},
            "cod_type": cod_type,
            "plot_ids": {
                "valid": valid_filter["plot_ids"],
                "invalid": invalid_filter["plot_ids"],
            },
        }

        # if no valid or invalid data, turn off timeframe
        if (len(valid_filter["ids"]) == 0) and (len(invalid_filter["ids"]) == 0):
            disable_timeframe = True

        return json.dumps(combined_filter_dict), disable_timeframe


# helper method to get filter ids given adjacent plot regions
def _get_filter_dict(
    va_df,
    selected_json,
    timeframe="all",
    search_terms=[],
    locations=None,
    location_types=None,
):

    filter_df = va_df.copy()
    granularity = INITIAL_GRANULARITY
    plot_ids, plot_regions = list(), list()

    filter_dict = {
        "geo_filter": (selected_json is not None) or (len(search_terms) > 0),
        "plot_regions": [],
        "chosen_region": "all",
        "ids": [],
        "plot_ids": [],
    }
    if filter_dict["geo_filter"]:
        # first, check if user searched anything. If yes, use that as filter.
        if search_terms is not None:
            if len(search_terms) > 0:
                search_terms = (
                    [search_terms] if isinstance(search_terms, str) else search_terms
                )
                granularity = locations.get(search_terms[0], granularity)
                filter_df = filter_df[filter_df[granularity].isin(set(search_terms))]
                filter_dict["chosen_region"] = search_terms[0]

        # then, check for locations clicked on map.
        if selected_json is not None:
            point_df = pd.DataFrame(selected_json["points"])
            chosen_regions = point_df["location"].tolist()
            granularity = locations.get(chosen_regions[0], granularity)
            filter_df = filter_df[filter_df[granularity].isin(set(chosen_regions))]
            filter_dict["chosen_region"] = chosen_regions[0]

        # get parent location type from current granularity
        parent_location_type = shift_granularity(
            granularity, location_types, move_up=True
        )

        # get all adjacent regions (siblings) to chosen region(s) for plotting
        for parent_name in filter_df[parent_location_type].unique():
            # get ids of vas in parent region
            va_ids = va_df[va_df[parent_location_type] == parent_name].index.tolist()
            plot_ids = plot_ids + va_ids
            location_object = Location.objects.get(name=parent_name)
            children = location_object.get_children()
            children_names = [c.name for c in location_object.get_children()]
            plot_regions = plot_regions + children_names + [parent_name]
            # set final granularity to same level of children
            granularity = children[0].location_type

    # finally, apply time filter if necessary
    if timeframe != "all":
        cutoff = dt.datetime.today() - dt.timedelta(days=LOOKUP["time_dict"][timeframe])
        filter_df = filter_df[filter_df["date"] >= cutoff]

    filter_dict["plot_regions"] = plot_regions
    filter_dict["plot_ids"] = plot_ids
    filter_dict["ids"] = filter_df.index.tolist()
    filter_dict["granularity"] = granularity

    return filter_dict


# try to move one level up or down in the geographical hierarchy. If not possible,
# return current level
def shift_granularity(current_granularity, levels, move_up=False):
    current_granularity = current_granularity.lower()
    if current_granularity in levels:
        current_idx = levels.index(current_granularity)
        if move_up:
            new_idx = max(current_idx - 1, 0)
        else:
            new_idx = min(current_idx + 1, len(levels) - 1)
        return levels[new_idx]


# =========Map Metrics =======================#
# Top metrics to track for map dropdown
@app.callback(
    Output(component_id="cod_type", component_property="options"),
    [
        Input(component_id="va_data", component_property="children"),
        Input(component_id="filter_dict", component_property="children"),
    ],
)
def get_metrics(va_data, filter_dict=None, N=10):
    # by default, start with aggregate measures
    metrics = []
    metric_data = pd.read_json(va_data)
    if metric_data.size > 0:
        if filter_dict is not None:
            filter_dict = json.loads(filter_dict)
            metric_data = metric_data.iloc[filter_dict["ids"]["valid"], :]
            # only load options if remaining data after filter
            if metric_data.size > 0:
                # add top N CODs by incidence to metric list
                metrics = ["all"] + (
                    metric_data["cause"]
                    .value_counts()
                    .sort_values(ascending=False)
                    .head(N)
                    .index.tolist()
                )

    return [{"label": LOOKUP["metric_names"].get(m, m), "value": m} for m in metrics]


def get_metric_display_names(map_metrics):
    names = []
    for metric in map_metrics:
        metric_name = LOOKUP["metric_names"].get(metric, None)
        if metric_name is None:
            metric_name = " ".join([x.capitalize() for x in metric.strip().split(" ")])
        names.append(metric_name)
    return names


# ====================Geographic Levels (View options)============#
@app.callback(
    [
        Output(component_id="view_level", component_property="options"),
        Output(component_id="view_level", component_property="disabled"),
        Output(component_id="view_label", component_property="className"),
    ],
    [
        Input(component_id="filter_dict", component_property="children"),
        Input(component_id="location_types", component_property="children"),
    ],
)
def update_view_options(filter_dict, location_types):
    if filter_dict is not None:
        filter_dict = json.loads(filter_dict)

        # only activate this dropdown when user is zoomed out
        disable = filter_dict["geo_filter"]
        if not disable:
            view_options = json.loads(location_types)
            label_class = "input-label"
        else:
            view_options = []
            label_class = "input-label-disabled"
        options = [{"label": o.capitalize(), "value": o} for o in view_options]
        return options, disable, label_class


# when view dropdown is disabled, reset selected value to null
@app.callback(
    Output(component_id="view_level", component_property="value"),
    [Input(component_id="view_level", component_property="disabled"),],
)
def reset_view_value(is_disabled=False):
    if is_disabled:
        return ""

    raise dash.exceptions.PreventUpdate


# ====================Map Logic===================================#
@app.callback(
    #   [
    Output(component_id="choropleth-container", component_property="children"),
    #        Output(component_id="bounds", component_property="children")
    #    ],
    [
        Input(component_id="va_data", component_property="children"),
        Input(component_id="timeframe", component_property="value"),
        Input(component_id="cod_type", component_property="value"),
        Input(component_id="view_level", component_property="value"),
        Input(component_id="location_types", component_property="children"),
        Input(component_id="filter_dict", component_property="children"),
    ],
)
def update_choropleth(
    va_data,
    timeframe,
    cod_type="All",
    view_level=None,
    location_types=None,
    filter_dict=None,
    geojson=GEOJSON,
    zoom_in=False,
):
    # first, see which input triggered update. If granularity change, only run
    # if value is non-empty
    context = dash.callback_context
    trigger = context.triggered[0]
    if trigger["prop_id"].split(".")[0] == "view_level" and trigger["value"] == "":
        raise dash.exceptions.PreventUpdate
    figure = go.Figure()
    config = None
    if va_data is not None:
        # initialize variables
        all_data = pd.read_json(va_data)
        plot_data = all_data.copy()
        return_value = html.Div(id="choropleth")
        granularity = INITIAL_GRANULARITY
        location_types = json.loads(location_types)
        include_no_datas = True
        ret_val = dict()
        border_thickness = 0.25  # thickness of borders on map
        # name of column to plot
        data_value = (
            "age_mean" if len(re.findall("[mM]ean", cod_type)) > 0 else "age_count"
        )

        if plot_data.size > 0:
            timeframe = timeframe.lower()
            feature_id = "properties.area_name"
            plot_geos = geojson["features"]

            # if dashboard filter applied, carry over to data
            if filter_dict is not None:
                filter_dict = json.loads(filter_dict)
                granularity = filter_dict.get("granularity", granularity)
                # only proceed if filter is non-empty

                plot_data = plot_data.iloc[filter_dict["ids"]["valid"], :]
                # only proceed with filter if remaining data after filter
                if plot_data.size > 0:
                    ret_val["filter_dict"] = filter_dict
                    # geo_filter is true if user clicked on map or searches for location
                    zoom_in = filter_dict["geo_filter"]

                    # if zoom in necessary, filter geojson to only chosen region(s)
                    if zoom_in:

                        # if user has clicked on map, try to zoom into a finer granularity
                        granularity = shift_granularity(
                            granularity, location_types, move_up=False
                        )

                        # filter geojson to match plotting regions
                        plot_regions = filter_dict["plot_regions"]
                        plot_geos = [
                            g
                            for g in geojson["features"]
                            if g["properties"]["area_name"] in plot_regions
                        ]
                        chosen_region = plot_data[granularity].unique()[0]
                        # if adjacent_ids specified, and data exists for these regions, plot them on map first
                        plot_ids = filter_dict["plot_ids"]["valid"]
                        #                    ret_val["plot_ids"] = plot_ids
                        if len(plot_ids) > 0:
                            adjacent_data = all_data.iloc[plot_ids, :].loc[
                                all_data[granularity] != chosen_region
                            ]

                            if adjacent_data.size > 0:

                                # background plotting - adjacent regions
                                adjacent_map_df = generate_map_data(
                                    adjacent_data,
                                    plot_geos,
                                    granularity,
                                    zoom_in,
                                    cod_type,
                                )
                                figure = add_trace_to_map(
                                    figure,
                                    adjacent_map_df,
                                    geojson,
                                    theme_name="secondary",
                                    z_col=data_value,
                                    location_col=granularity,
                                )
                                # only plot non-empty regions in main layer so as not to hide secondary layer
                                include_no_datas = False
                                border_thickness = 2 * border_thickness

            if cod_type != "all":
                plot_data = plot_data[plot_data["cause"] == cod_type]

            # only proceed if there's data
            if plot_data.size > 0:

                # if user has not chosen a view level or its disabled, default to using granularity
                view_level = view_level if len(view_level) > 0 else granularity

                # get map tooltips to match view level (disstrict or province)
                map_df = generate_map_data(
                    plot_data,
                    plot_geos,
                    view_level,
                    zoom_in,
                    cod_type,
                    include_no_datas,
                )

                # Set plot title to Total VAs if cod_type=='all'
                cod_title = "Total VAs" if cod_type == "all" else cod_type.capitalize()

                highlight_region = map_df.shape[0] == 1
                if highlight_region:
                    # increse border thickness to highlight selcted region
                    border_thickness = 3 * border_thickness

                figure.add_trace(
                    go.Choropleth(
                        locations=map_df[view_level],
                        z=map_df[data_value].astype(float),
                        locationmode="geojson-id",
                        geojson=geojson,
                        featureidkey=feature_id,
                        colorscale=LOOKUP["colorscales"]["primary"],
                        hovertext=map_df["tooltip"],
                        hoverinfo="text",
                        autocolorscale=False,
                        marker_line_color=LOOKUP["line_colors"][
                            "primary"
                        ],  # line markers between states
                        marker_line_width=border_thickness,
                        colorbar=dict(
                            title="{}<br>by {}".format(
                                cod_title, view_level.capitalize()
                            ),
                            thicknessmode="fraction",
                            thickness=0.03,
                            lenmode="fraction",
                            len=0.8,
                            yanchor="middle",
                            ticks="outside",
                            nticks=10,
                        ),
                    )
                )

                # update figure layout
                figure.update_layout(
                    margin={"r": 0, "t": 0, "l": 0, "b": 0},
                    # clickmode="event" if zoom_in else "event+select",
                    clickmode="event+select",
                    dragmode="pan",
                )
                # additional styling
                config = graph_config
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
        ret_val = json.dumps(filter_dict)
    return_value = dcc.Graph(id="choropleth", figure=figure, config=graph_config)

    return return_value  # , json.dumps(ret_val)


# ==========Helper method to plot adjacent regions on map =====#
def add_trace_to_map(
    figure,
    trace_data,
    geojson,
    trace_type=go.Choropleth,
    feature_id=None,
    location_col=None,
    z_col=None,
    tooltip_col=None,
    theme_name=None,
):

    feature_id = "properties.area_name" if not feature_id else feature_id
    location_col = "locations" if not location_col else location_col
    z_col = "z_value" if not z_col else z_col
    tooltip_col = "tooltip" if not tooltip_col else tooltip_col
    theme_name = "secondary" if not theme_name else theme_name

    trace = trace_type(
        locations=trace_data[location_col],
        z=trace_data[z_col].astype(float),
        locationmode="geojson-id",
        geojson=geojson,
        featureidkey=feature_id,
        hovertext=trace_data[tooltip_col],
        hoverinfo="text",
        colorscale=LOOKUP["colorscales"][theme_name],
        marker_line_color=LOOKUP["line_colors"][theme_name],
        marker_line_width=0.25,
        showscale=False,
    )
    figure.add_trace(trace)

    return figure


# ==========Map dataframe (built from va dataframe)============#
def generate_map_data(
    va_df,
    chosen_geojson,
    view_level="district",
    zoom_in=False,
    metric="All",
    include_no_datas=True,
):
    if va_df.size > 0:
        map_df = (
            va_df[[view_level, "age", "location"]]
            .groupby(view_level)
            .agg({"age": ["mean", "count"], "location": [pd.Series.nunique]})
        )

        map_df.columns = ["_".join(tup) for tup in map_df.columns.to_flat_index()]
        map_df.reset_index(inplace=True)

        # generate tooltips for regions with data
        metric_name = LOOKUP["metric_names"].get(metric, metric)
        map_df["age_mean"] = np.round(map_df["age_mean"], 1)
        map_df["tooltip"] = (
            "<b>"
            + map_df[view_level]
            + "</b>"
            + "<br>"
            + f"<b>{metric_name}: </b>"
            + map_df["age_count"].astype(str)
            + "<br>"
            + "<b>Mean Age of Death: </b>"
            + map_df["age_mean"].astype(str)
            + "<br>"
            + "<b>Active Facilities: </b>"
            + map_df["location_nunique"].astype(str)
        )

        # join with all region names to ensure each region has a record
        chosen_region_names = [
            (f["properties"]["area_name"], f["properties"]["area_id"])
            for f in chosen_geojson
            if f["properties"]["area_level_label"] == view_level.capitalize()
        ]
        geo_df = pd.DataFrame.from_records(
            chosen_region_names, columns=[view_level, "area_id"]
        )
        # if plot_all_geos is True, include all geos, regardless of their data status.
        join_type = "left" if include_no_datas else "inner"
        map_df = geo_df.merge(map_df, how=join_type, on=view_level)

        # fill NAs with 0s and rename empty tooltips to "No Data"
        # map_df["tooltip"].fillna("No Data", inplace=True)
        map_df["tooltip"] = map_df.apply(
            lambda row: f"<b>{row[view_level]}</b><br>No Data"
            if pd.isnull(row["tooltip"])
            else row["tooltip"],
            axis=1,
        )
        map_df.fillna(0, inplace=True)

        return map_df
    return pd.DataFrame()


# =========Callout Boxes Logic============================================#
@app.callback(
    Output(component_id="callout-container", component_property="children"),
    [
        Input(component_id="va_data", component_property="children"),
        Input(component_id="invalid_va_data", component_property="children"),
        Input(component_id="timeframe", component_property="value"),
        Input(component_id="filter_dict", component_property="children"),
    ],
)
def update_callouts(
    va_data, invalid_va_data, timeframe, filter_dict=None, geojson=GEOJSON
):
    coded_vas, uncoded_vas, active_facilities, num_field_workers, coverage = (
        0,
        0,
        0,
        0,
        0,
    )
    if va_data is not None:
        plot_data = pd.read_json(va_data)

        invalid_va_data = pd.read_json(invalid_va_data)
        granularity = INITIAL_GRANULARITY
        if plot_data.size > 0:
            if filter_dict is not None:
                filter_dict = json.loads(filter_dict)
                plot_data = plot_data.iloc[filter_dict["ids"]["valid"], :]
                invalid_va_data = invalid_va_data.iloc[filter_dict["ids"]["invalid"], :]
                granularity = filter_dict.get("granularity", granularity)

            # total valid (coded) VAs
            coded_vas = plot_data.shape[0]

            # total invalid (uncoded) VAs
            uncoded_vas = invalid_va_data.shape[0]

            # active facilities
            active_facilities = plot_data["location"].nunique()

            # TODO: get field worker data from ODK - this is just a janky hack
            num_field_workers = int(1.25 * active_facilities)

            # region 'representation' (fraction of chosen regions that have VAs)
            total_regions = geojson[f"{granularity}_count"]

            if filter_dict is not None:
                if len(filter_dict["plot_regions"]) > 0:
                    total_regions = len(filter_dict["plot_regions"])

                    # TODO: fix this to be more generic
                    if granularity == "province":
                        granularity = "district"
            regions_covered = (
                plot_data[[granularity, "age"]].dropna()[granularity].nunique()
            )
            coverage = "{}%".format(np.round(100 * regions_covered / total_regions, 0))

    return [
        make_card(coded_vas, header="Coded VAs"),
        make_card(uncoded_vas, header="Uncoded VAs"),
        make_card(active_facilities, header="Active Facilities"),
        make_card(num_field_workers, header="Field Workers"),
        make_card(coverage, header="Region Representation"),
    ]


# build a calloutbox with specific value
# colors: primary, secondary, info, success, warning, danger, light, dark
def make_card(
    value, header=None, description="", color="light", inverse=False, style=None
):
    card_content = []
    if header is not None:
        card_content.append(dbc.CardHeader(header, style={"padding": ".5rem"}))
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


# =========Demographic plot logic==============================================#
@app.callback(
    Output(component_id="demos-container", component_property="children"),
    [
        Input(component_id="va_data", component_property="children"),
        Input(component_id="timeframe", component_property="value"),
        Input(component_id="filter_dict", component_property="children"),
    ],
)
def demographic_plot(va_data, timeframe, filter_dict=None):
    figure = go.Figure()
    if va_data is not None:
        plot_data = pd.read_json(va_data)
        if plot_data.size > 0:
            if filter_dict is not None:
                filter_dict = json.loads(filter_dict)
                plot_data = plot_data.iloc[filter_dict["ids"]["valid"], :]
                # if cod chosen, filter down to only vas with chosen cod
                if filter_dict["cod_type"].lower() != "all":
                    cod = filter_dict["cod_type"]
                    plot_data = plot_data[plot_data["cause"] == cod]
                    cod_title = LOOKUP["metric_names"].get(cod, cod)
                    plot_title = f"{cod_title} Demographics"
                else:
                    plot_title = "All-Cause Demographics"
            figure = plotting.demographic_plot(plot_data, title=plot_title)
    return dcc.Graph(id="demos_plot", figure=figure, config=chart_config)


# =========Cause of Death Plot Logic============================================#
@app.callback(
    Output(component_id="cod-container", component_property="children"),
    [
        Input(component_id="va_data", component_property="children"),
        Input(component_id="timeframe", component_property="value"),
        Input(component_id="cod_factor", component_property="value"),
        Input(component_id="cod_n", component_property="value"),
        Input(component_id="filter_dict", component_property="children"),
    ],
)
def cod_plot(va_data, timeframe, factor="All", N=10, filter_dict=None):
    figure = go.Figure()
    if va_data is not None:
        plot_data = pd.read_json(va_data)
        if plot_data.size > 0:
            if filter_dict is not None:
                filter_dict = json.loads(filter_dict)
                cod = filter_dict["cod_type"]
                plot_data = plot_data.iloc[filter_dict["ids"]["valid"], :]

            # only proceed if remaining data after filter
            if plot_data.size > 0:
                figure = plotting.cause_of_death_plot(
                    plot_data, factor=factor, N=N, chosen_cod=cod
                )
    return dcc.Graph(id="cod_plot", figure=figure, config=chart_config)


#
#
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
    if va_data is not None:
        plot_data = pd.read_json(va_data)
        if plot_data.size > 0:
            if filter_dict is not None:
                filter_dict = json.loads(filter_dict)
                cod = filter_dict["cod_type"]
                cod_title = LOOKUP["metric_names"].get(cod, cod)
                plot_data = plot_data.iloc[filter_dict["ids"]["valid"], :]
                if filter_dict["cod_type"].lower() != "all":
                    plot_data = plot_data[plot_data["cause"] == filter_dict["cod_type"]]
                plot_title = f"{cod_title} Trend by {group_period}"
            # only run if remaining data after filter
            if plot_data.size > 0:
                figure = plotting.va_trend_plot(
                    plot_data, group_period, factor, title=plot_title
                )
    return dcc.Graph(id="trend_plot", figure=figure, config=chart_config)


# uncomment this if running as Dash app (as opposed to DjangoDash app)
# app.run_server(debug= True)
