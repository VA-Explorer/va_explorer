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
import logging

import dash
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
import numpy as np
import pandas as pd
import plotly.graph_objs as go
from dash.dependencies import Input, Output
from django_plotly_dash import DjangoDash
from django.urls import reverse


from va_explorer.va_logs.logging_utils import write_va_log
from va_explorer.va_data_management.models import Location
from va_explorer.va_analytics.utils import plotting, loading, rendering

# ================APP DEFINITION===============#
# NOTE: to include external stylesheets, set external_stylesheets parameter in constructor
# app = dash.Dash(__name__)  # Dash constructor
app = DjangoDash(
        name="va_dashboard",
        serve_locally=True,
        add_bootstrap_links=True,
  )


# NOTE: moved Toolbar configurations to plotting.py

# ===========INITIAL CONFIG VARIABLES=============#
# initial timeframe for map data to display
INITIAL_TIMEFRAME = "all"
# folder where all data and settings local to app are kept
DATA_DIR = "va_explorer/va_analytics/dash_apps/dashboard_data"
# Zambia Geojson pulled from: https://adr.unaids.org/dataset/zambia-geographic-data-2019
JSON_FILE = "zambia_geojson.json"
# initial granularity
INITIAL_GRANULARITY = "province"
# initial metric to plot on map
INITIAL_COD_TYPE = "all"
# event logger to track key dashboard events
LOGGER = logging.getLogger("event_logger")
import time
START_TIME = time.time()

# ============Lookup dictionaries =================#
LOOKUP = plotting.load_lookup_dicts()
COD_GROUPS = plotting.load_cod_groupings(data_dir=DATA_DIR)

# =============Geo dictionaries ========#
GEOJSON = loading.load_geojson_data(json_file=f"{DATA_DIR}/{JSON_FILE}")

# ===============APP LAYOUT====================#
app.layout = html.Div(
    id="app-body-container",
    children=[
        html.Div(

            [
                html.Div(id="va_update_stats"),
                # global filters (affect entire dashboard)
                dbc.Row(
                    [
                        html.Div(id="dashboard-title", children=html.Span("Analytics Dashboard", className="dashboard-title")),
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
                                            "Last 3 Months",
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
                                    id="download_data_div",
                                    className="dashboard-comp-container",
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
                                                "width": "80%",
                                            },
                                        ),
                                         html.Div(
                                            className="dashboard-comp-container",
                                            children=[
                                                dcc.Dropdown(
                                                    id="view_level",
                                                    # value="",
                                                    value=INITIAL_GRANULARITY,
                                                    placeholder="View",
                                                    style={
                                                        "margin-bottom": "5px",
                                                        "width": "100px",
                                                    },
                                                    searchable=False,
                                                    clearable=False,
                                                    disabled=False,
                                                ),
                                            ],
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
                                            children=dcc.Graph(id="choropleth"),
                                        )
                                    ],
                                ),
                                html.Div(id="bounds"),
                                
                                # data stores
                                dcc.Store(id="va_data"),
                                dcc.Store(id="invalid_va_data"),
                                dcc.Store(id="locations"),
                                dcc.Store(id="location_types"),
                                dcc.Store(id="filter_dict"),
                                dcc.Store(id="display_names"),
                                dcc.Store(id="cod_type_data"),
                                dcc.Store(id="timeframe_data"),
                                dcc.Store(id="geojson_data", data=GEOJSON),
                                dcc.Store(id="callout-container-data"),
                                dcc.Store(id="granularity", data={"granularity":INITIAL_GRANULARITY}),

                                # used to trigger data ingest when page first loads
                                html.Div(id="hidden_trigger", style={"display": "none"})
                            ],
                            width=7,
                            style={"min-width": "480px", "margin-bottom": "15px"},
                        ),
                        dbc.Col(
                            [
                                dcc.Tabs(
                                    id="plot_tabs",
                                    children=[  # graph tabs
                                        dcc.Tab(
                                            id="cod_tab",
                                            label="COD Analysis",
                                            children=[  # tab 1: COD Analysis
                                                html.Div(
                                                    id="cod_buttons",
                                                    children=[
                                                        dbc.Row(
                                                            [
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
                                                                ),
    
                                                                # COD groups dropdown
                                                                dbc.Col([
                                                                            dcc.Dropdown(
                                                                             id='cod_group',
                                                                             options=[
                                                                                {
                                                                                    "label": LOOKUP['display_names'].get(o,o.capitalize()), 
                                                                                    "value": o,                                                                                         
                                                                                }
                                                                                for o in ['All CODs'] + COD_GROUPS.columns[2:].tolist()
                                                                            ], 
                                                                            value='All CODs', 
                                                                            style={
                                                                                "margin-top": "5px",
                                                                                "margin-bottom": "5px",
                                                                            },
                                                                            searchable=True,
                                                                            clearable=False,
                                                                            multi=True,
                                                                                    
                                                                            )
                                                                            ], width=5),
                                                                # COD factor (demographic) dropdown
                                                                dbc.Col([
                                                                        dcc.Dropdown(
                                                                            id="cod_factor",
                                                                            options=[
                                                                                {
                                                                                    "label": "By {}".format(o) if o != "Overall" else o,
                                                                                    "value": o,
                                                                                }
                                                                                for o in [
                                                                                    "Overall",
                                                                                    "Age Group",
                                                                                    "Sex",
                                                                                    "Place of Death",
                                                                                ]
                                                                            ],
                                                                            value="Overall",
                                                                            style={
                                                                                "margin-top": "5px",
                                                                                "margin-bottom": "5px",
                                                                                "width": "150px",
                                                                            },
                                                                            searchable=False,
                                                                            clearable=False,
                                                                        ),
                                                                    ],
                                                                    width=4,
                                                                ),
                                                            ],
                                                            style={"margin-top": "5px"}
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
                                            id="demographic_tab",
                                            children=[
                                                dcc.Loading(
                                                    html.Div(id="demos-container"),
                                                    type="circle",
                                                )
                                            ],
                                        ),
                                        dcc.Tab(
                                            label="VA Trends",
                                            id="trend_tab",
                                            children=[
                                                html.Div(
                                                    id="ts_buttons",
                                                    children=[
                                                        dbc.Row(
                                                            [
                                                                html.Div(
                                                                        className="dashboard-comp-container",
                                                                        children=[
                                                                            dcc.Dropdown(
                                                                                 id='ts_search',
                                                                                options = [{"label": "All Causes", "value": "All causes.all"}],
                                                                                placeholder = "Search COD Keywords",
                                                                                style={
                                                                                    "margin-top": "5px",
                                                                                    "margin-bottom": "5px",
                                                                                    "width": "250px"
                                                                                },
                                                                                searchable=True,
                                                                                clearable=True,
                                                                                multi=True,
                                                                                value="All causes.all"
                                                                                                
                                                                            )]
                                                                ),
                                                                html.Div(
                                                                        className="dashboard-comp-container",
                                                                        children=[
                                                                        dcc.Dropdown(
                                                                            id="ts_factor",
                                                                            options=[
                                                                                {
                                                                                    "label": "By {}".format(o) if o != "Overall" else o,
                                                                                    "value": o,
                                                                                }
                                                                                for o in [
                                                                                    "Overall",
                                                                                    "Age Group",
                                                                                    "Sex",
                                                                                    "Place of Death",
                                                                                ]
                                                                            ],
                                                                            value="Overall",
                                                                            style={
                                                                                "margin-top": "5px",
                                                                                "margin-bottom": "5px",
                                                                                "width": "150px",
                                                                            },
                                                                            searchable=False,
                                                                            clearable=False,
                                                                        )
                                                                    ]
                                                                ),

                                                            html.Div(
                                                                    className="dashboard-comp-container",
                                                                    children=[
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
                                                                       ]
                                                                )

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
                            width=5,
                            style={"min-width": "480px", "margin-bottom": "15px", "margin-top": "40px"},
                        ),
                    ],
                ),
            ]
        )
    ],
)


# =============Reset logic (reset map to default)====================#
# callback 1
# @app.callback(
#     [
#         Output(component_id="map_search", component_property="value"),
#         Output(component_id="cod_type", component_property="value"),
#         Output(component_id="timeframe", component_property="value"),
#     ],
#     [Input(component_id="reset", component_property="n_clicks")],
# )

# def reset_dashboard(n_clicks=0, **kwargs):
#     START_TIME = time.time()
#     write_va_log(LOGGER, f"[dashboard] Clicked Reset Button", kwargs["request"])
#     print("Hidden Callback", time.time() - START_TIME)
#     return "", INITIAL_COD_TYPE, INITIAL_TIMEFRAME

### client-side conversions for reset_dashboard ###
### (note we have 3 because only 1 output at a time with Django-plotly-dash) ###
app.clientside_callback(
    """
    function(n_clicks){
        return ""
    }
    """,
    Output(component_id="map_search", component_property="value"),
    [Input(component_id="reset", component_property="n_clicks")]
)
app.clientside_callback(
    """
    function(n_clicks, cod_type){
        return cod_type
    }
    """,
    Output(component_id="cod_type", component_property="value"),
    [Input(component_id="reset", component_property="n_clicks"),
     Input(component_id="cod_type_data", component_property="data")
    ]
)
app.clientside_callback(
    """
    function(n_clicks, timeframe){
        return timeframe
    }
    """,
    Output(component_id="timeframe", component_property="value"),
    [Input(component_id="reset", component_property="n_clicks"),
    Input(component_id="timeframe_data", component_property="data")
    ]
)




# ============ VA data (loaded from database and shared across components) ========
'''
Note on the use of expanded_callback in django_plotly_dash

The expanded_callback gives us access to additional arguments passed as kwargs, including
the Django user instance.

As per documentation:
This function registers the callback function, and sets an internal flag that mandates that
ALL callbacks are passed the enhanced arguments

Thus, we must add **kwargs to all callbacks in the app, even though they are not explicitly
designated as "expanded"
'''
# callback 2
@app.expanded_callback(
    [
        Output(component_id="va_data", component_property="data"),
        Output(component_id="invalid_va_data", component_property="data"),
        Output(component_id="locations", component_property="data"),
        Output(component_id="location_types", component_property="data"),
        Output(component_id="map_search", component_property="options"), # map search options
        Output(component_id="ts_search", component_property="options"), # search options for VA trends
        Output(component_id="download_data_div", component_property="children"), #download button
        Output(component_id="va_update_stats", component_property="children"), # stats on last update
        Output(component_id="display_names", component_property="data"),
        Output(component_id="cod_type_data", component_property="data"),
        Output(component_id="timeframe_data", component_property="data")

    ],
    [Input(component_id="hidden_trigger", component_property="children")],
)

def init_va_data(hidden_trigger=None, **kwargs):
    START_TIME = time.time()
    date_cutoff=None
    timeframe = LOOKUP["time_dict"].get(INITIAL_TIMEFRAME, "all")
    if timeframe != "all":
        date_cutoff = dt.datetime.today() - dt.timedelta(timeframe)

    res = loading.load_va_data(kwargs['user'], date_cutoff=date_cutoff)    

    # all VAs with required fields for dashboard (COD, date of death, location). 
    valid_va_data = res["data"]["valid"].to_dict()
    # strips out numeric cod codes in front of COD names
    valid_va_data["cause"] = { k:v.lstrip('0123456789.- ') for k, v in valid_va_data["cause"].items()}

    # all VAs without a COD assignment
    invalid_va_data = res["data"]["invalid"].to_dict()
    # list of locations used in dashboard
    locations = res.get("locations", [])
    # geographical hierarchy (ex. Province -> District -> Facility)
    location_types = res.get("location_types", {})
    # map search options
    search_options = [{"label": location, "value": location} for location in locations.keys()]

    # trend search options
    raw_ts_options = plotting.load_ts_options(res["data"]["valid"], cod_groups=COD_GROUPS)
    ts_options =  [{"label": LOOKUP["display_names"].get(name, name.capitalize()),
                             "value": f"{name}.{type}"} for name, type in raw_ts_options] 

    # statistics on when data was last updated/submitted
    update_stats = res.get("update_stats", None)
    update_div = rendering.render_update_header(update_stats)

    # Download button logic.
    # Only show the Download Data button if user has access to it.
    download_div = html.Div(id="download_data_div")
    download_div.children = [
        dbc.Button(children=[html.I(className="fas fa-download"),
                    html.Span(" Data", style={"margin-left": "2px"})],
                    id="download_button", href=reverse("va_export:va_api"), color="primary",
                    external_link=True) 

    ]
    # hide download data button if user doesn't have permission to download
    download_div.hidden = (not kwargs["user"].can_download_data)
    print("Hidden Callback", time.time() - START_TIME)
    return valid_va_data, invalid_va_data, locations, location_types, search_options, ts_options, download_div, update_div, LOOKUP["display_names"], INITIAL_COD_TYPE, INITIAL_TIMEFRAME

# ============ Location search options (loaded after load_va_data())==================
# callback 3
# @app.callback(
#     Output(component_id="log_data", component_property="children"),
#     [Input(component_id="plot_tabs", component_property="value")]

# )
# def log_tab_value(tab_value, **kwargs):
#     START_TIME = time.time()
#     tab_names = {"tab-1": "COD", "tab-2": "Demographics", "tab-3": "VA Trends"}
#     tab_name = tab_names.get(tab_value, None)
#     if tab_name:
#         write_va_log(LOGGER, f"[dashboard] Clicked on {tab_name} Tab ", kwargs["request"])
#         print("log tab value Callback", time.time() - START_TIME)
#         return tab_name

### client-side conversion for log_tab_value ###
app.clientside_callback(
"""
    function(tab_value, scale) {
        var tab_names = {"tab-1": "COD", "tab-2": "Demographics", "tab-3": "VA Trends"};
        var tab_name = tab_names[tab_value];
        return(tab_name);
        
    }
    """,
    Output(component_id="log_data", component_property="children"),
    [Input(component_id="plot_tabs", component_property="value")]
)

## HARD TO UPDATE
# ============ Filter logic (update filter table used by other componenets)========#
# callback 4
@app.callback(
    [
        Output(component_id="filter_dict", component_property="data"),
        Output(component_id="dashboard-title", component_property="children"),
        Output(component_id="download_button", component_property="href")
    ],
    [
        Input(component_id="va_data", component_property="data"),
        Input(component_id="invalid_va_data", component_property="data"),
        Input(component_id="choropleth", component_property="selectedData"),
        Input(component_id="timeframe", component_property="value"),
        Input(component_id="cod_type", component_property="value"),
        Input(component_id="map_search", component_property="value"),
        Input(component_id="locations", component_property="data"),
        Input(component_id="location_types", component_property="data"),
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
    **kwargs
):
    START_TIME = time.time()
    if va_data is not None:
        valid_va_df = pd.DataFrame(va_data)
        valid_va_df["date"] = pd.to_datetime(valid_va_df["date"])
        invalid_va_df = pd.DataFrame(invalid_va_data)
        invalid_va_df["date"] = pd.to_datetime(invalid_va_df["date"])
        search_terms = [] if search_terms is None else search_terms
        
        # get user location restrictions. If none, will return an empty queryset
        location_restrictions = list(kwargs["user"].location_restrictions.values("name", "id"))
            
        # if no selected json, convert to empty dictionary for easier processing
        selected_json = {} if not selected_json else selected_json

        # filter valid vas (VAs with COD)
        valid_filter = _get_filter_dict(
            valid_va_df,
            selected_json,
            timeframe=timeframe,
            location_types=location_types,
            search_terms=search_terms,
            locations=locations,
            restrictions=location_restrictions
        )
        # filter invalid vas (VAs without COD)
        invalid_filter = _get_filter_dict(
            invalid_va_df,
            selected_json,
            timeframe=timeframe,
            location_types=location_types,
            search_terms=search_terms,
            locations=locations,
            restrictions=location_restrictions
        )     

        # Dashboard title logic. If field worker, make clear it's just their VAs. Otherwise, 
        # If particular region chosen, add to title. 
        if kwargs["user"].is_fieldworker():
            title = "COD Analytics for Your VAs"
        elif valid_filter["chosen_region"]["name"].lower().startswith("all"):
            title = "COD Analytics for All Regions"
        else:
            title = f"COD Analytics for {valid_filter['chosen_region']['name']}"
        dashboard_title = html.Span(title, className="dashboard-title")

        # combine filter information into dictionary to share across other callbacks
        combined_filter_dict = {
            "plot_regions": valid_filter["plot_regions"],  # same across both dicts
            "granularity": valid_filter["granularity"],  # same across both dictionaries
            "search_filter": valid_filter["search_filter"], # same across both dictionaries
            "geo_filter": valid_filter["geo_filter"],  # same across both dictionaries
            "chosen_region": valid_filter["chosen_region"],  # same across both dictionaries
            "ids": {"valid": valid_filter["ids"], "invalid": invalid_filter["ids"]},
            "cod_type": cod_type,
            "plot_ids": {
                "valid": valid_filter["plot_ids"],
                "invalid": invalid_filter["plot_ids"],
            },
        }

        # build download url based on params above
        if type(combined_filter_dict["chosen_region"]) is dict:
            chosen_region = combined_filter_dict["chosen_region"]["name"]
        else:
            chosen_region = combined_filter_dict["chosen_region"]

        download_url = rendering.build_download_url(chosen_region=chosen_region, timeframe=timeframe,\
                                                    cod=cod_type, time_mapper=LOOKUP["time_dict"])
            
        log_callback_trigger(LOGGER, dash.callback_context, kwargs["request"])
        print("filter data Callback", time.time() - START_TIME)
        return combined_filter_dict , dashboard_title, download_url


def log_callback_trigger(logger, context, request):
    if context:
        trigger = context.triggered[0]
        if trigger:
            component_id = trigger["prop_id"].split(".")[0]
            # don't log entire filter dictionary
            if component_id != "filter_dict":
                # by default, set action and value to raw trigger values
                action = f"changed {component_id} to value "
                value = trigger["value"]
                # make message more specific for certain component callbacks
                if component_id == "choropleth":
                    action = "Zoomed in on region"
                    value = trigger["value"]["points"][0]["location"]
                elif component_id == "map_search":
                    action = "Searched for region"
                elif component_id == "cod_type":
                    action = "Changed COD Type to"
                elif component_id == "timeframe":
                    action = "Changed Timeframe to"
                
                write_va_log(logger, f"[dashboard] {action} {value}", request)
            
        

# helper method to get filter ids given adjacent plot regions
def _get_filter_dict(
    va_df,
    selected_json={},
    timeframe="all",
    search_terms=[],
    locations=None,
    location_types=None,
    restrictions=[]
):

    filter_df = va_df.copy()
    granularity = INITIAL_GRANULARITY
    plot_ids = plot_regions = list()
    
    filter_dict = {

        "geo_filter": any(map(lambda x: len(x) > 0, [restrictions, selected_json, search_terms])),
        "search_filter": (len(search_terms) > 0),
        "plot_regions": [],
        "chosen_region": {"name": "all"},
        "ids": [],
        "plot_ids": [],
    }
    
    if filter_dict["geo_filter"]:
        # first, check if geo filter is for location restrictions
        if len(restrictions) > 0:
            # TODO: make this work for more than one assigned region
            granularity = locations.get(restrictions[0]["name"], granularity)
            # no need to filter data, as that's already done in load_data
            chosen_region = restrictions[0]
            
            location_obj = Location.objects.get(pk=chosen_region["id"])
            # if assigned to a POI (i.e. lowest level of location hierarchy) move one level up
            #TODO: make this more generic to handle other location types
            if location_obj.location_type == "facility":
                # ancestors returned in descending order
                location_obj = location_obj.get_ancestors().last()
                chosen_region = location_obj.name
            # otherwise, just plot chosen region and descendants
            plot_regions = [r.name for r in location_obj.get_children()]
            plot_regions.append(chosen_region)

            plot_ids = filter_df.index.tolist()
            filter_dict["chosen_region"] = chosen_region

       # next, check if user searched anything. If yes, use that as filter.
        if search_terms is not None:
            if filter_dict["search_filter"]:
                search_terms = (
                    [search_terms] if isinstance(search_terms, str) else search_terms
                )
                granularity = locations.get(search_terms[0], granularity)
                filter_df = filter_df[filter_df[granularity].isin(set(search_terms))]
                filter_dict["chosen_region"] = {"name": search_terms[0]}

        # finally, check for locations clicked on map.
        if len(selected_json) > 0:
            point_df = pd.DataFrame(selected_json["points"])
            chosen_regions = point_df["location"].tolist()
            granularity = locations.get(chosen_regions[-1], granularity)
            filter_df = filter_df[filter_df[granularity].isin(set(chosen_regions))]
            filter_dict["chosen_region"] = {"name": chosen_regions[0]}
    
        # get all adjacent regions (siblings) to chosen region(s) for plotting. Dont run when user has geo restrictions
        if len(restrictions) == 0:
            
            # get parent location type from current granularity
            parent_location_type = shift_granularity(
                granularity, location_types, move_up=True
            )

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
        filter_df["date"] = pd.to_datetime(filter_df["date"])
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
# callback 5
# @app.callback(
#     Output(component_id="cod_type", component_property="options"),
#     [
#         Input(component_id="va_data", component_property="data"),
#         Input(component_id="filter_dict", component_property="data"),
#     ],
# )
# def get_metrics(va_data, filter_dict=None, N=10, **kwargs):
#     # by default, start with aggregate measures
#     # print(va_data)
#     START_TIME = time.time()
#     metrics = []
#     metric_data = pd.DataFrame(va_data)
#     if metric_data.size > 0:
#         if filter_dict is not None:
#             metric_data = metric_data.loc[filter_dict["ids"]["valid"], :]
#             # only load options if remaining data after filter
#             if metric_data.size > 0:
#                 # add top N CODs by incidence to metric list
#                 metrics = ["all"] + (
#                     metric_data["cause"]
#                     .value_counts()
#                     .sort_values(ascending=False)
#                     .head(N)
#                     .index.tolist()
#                 )
#     print("get metrics Callback", time.time() - START_TIME)
#     return [{"label": LOOKUP["display_names"].get(m, m), "value": m} for m in metrics]

### client-side conversion for get_metrics ###
app.clientside_callback(
    """
    function(va_data, filter_dict, display_names){
        var N = 10;
        // console.log(N);
        // console.log(_.uniq([3,4,3]));
        // by default, start with aggregate measures
        var metrics = [];
        // NEED TO FIND A CONVENINENT WAY TO ACCOMPLISH THIS...
        // console.log(va_data);
        // metric_data = pd.DataFrame(va_data)
        var metric_data= va_data
        //console.log(Object.values(metric_data['index']).length);
        if (Object.values(metric_data['index']).length > 0){
            //console.log("HURDLE ONE")
            if (filter_dict !== null){
                // var value_counts = {};
                // for(var i=0; i<Object.keys(metric_data['cause']).length; i++){
                    // if(filter_dict['ids']['valid'].includes(Object.keys(metric_data['cause'])[i])){
                    // if(filter_dict['ids']['valid'].includes(metric_data['cause'][i])){
                        //console.log("HURDLE 3")
                        // if(Object.keys(value_counts).includes(metric_data['cause'][i])){
                            // value_counts[metric_data['cause'][i]] = value_counts[metric_data['cause'][i]] + 1;
                        // }
                        // else{
                            // value_counts[metric_data['cause'][i]] = 1
                        // }
                    // }
                // }
                
                var abc = new Map(Object.entries(metric_data['cause']));
                
                abc = [...abc].map(([name, value]) => ({ name, value }))
                
                // alternative to for loop
                let filtered_array = _.filter(abc, function(o) {return filter_dict['ids']['valid'].includes(o.name);});
                
                let obj = _.countBy(filtered_array, (rec) => {return rec.value});
                
                const sorted = new Map(Object.entries(obj).sort((a, b) => b[1] - a[1]));
                
                // console.log([...sorted].map(([name, value]) => ({ name, value })));
                metrics = Array.from( sorted.keys() ).slice(0,N);
                metrics.unshift("all")
            }
        }


        var metrics_return = [];
        // console.log(metrics.length);
        // can we use a map here????
        for(var j=0; j<metrics.length; j++){
            if(display_names[metrics[j]] !== undefined){
                metrics_return.push({"label": display_names[metrics[j]], "value":metrics[j]});
            }
            else{
                metrics_return.push({"label": metrics[j], "value":metrics[j]});
            }
        }
        // console.log(metrics_return);

        // metrics_return = [...metrics].map([name] => ({"label":}))
        return(metrics_return)
    }
    """
    ,
    Output(component_id="cod_type", component_property="options"),
    [
        Input(component_id="va_data", component_property="data"),
        Input(component_id="filter_dict", component_property="data"),
        Input(component_id="display_names", component_property="data"),
    ]
)







## Not really necessary...get_metrics just references lookup directly
def get_metric_display_names(map_metrics):
    names = []
    for metric in map_metrics:
        metric_name = LOOKUP["display_names"].get(metric, None)
        if metric_name is None:
            metric_name = " ".join([x.capitalize() for x in metric.strip().split(" ")])
        names.append(metric_name)
    return names


# ====================Geographic Levels (View options)============#
# callback 6
# @app.callback(
#     [
#         Output(component_id="view_level", component_property="options"),
#         Output(component_id="view_level", component_property="disabled"),
#     ],
#     [
#         Input(component_id="filter_dict", component_property="data"),
#         Input(component_id="location_types", component_property="data"),
#     ],
# )
# def update_view_options(filter_dict, location_types, **kwargs):
#     START_TIME = time.time()
#     if filter_dict is not None:

#         # only activate when user is zoomed out and hasn't searched for anything
#         disable = (filter_dict["geo_filter"] or filter_dict["search_filter"])
#         if not disable:
#             view_options = location_types
#            # label_class = "input-label"
#         else:
#             view_options = []
#             #label_class = "input-label-disabled"
#         options = [{"label": o.capitalize(), "value": o} for o in view_options]
#         print("update view Callback", time.time() - START_TIME)
#         return options, disable #, label_class

### Conversion of update_view_options to client-side callbacks ###
### have to use two different callbacks since we can only have one output in each (django-plotly-dash constraint)
app.clientside_callback(
    """
    function(filter_dict){
        if(filter_dict){
            // console.log(filter_dict);
            return((filter_dict['geo_filter'] === true) || (filter_dict['search_filter'] === true));
        }
        return null;
    }
    """,
    Output(component_id="view_level", component_property="disabled"),
    [Input(component_id="filter_dict", component_property="data")]

)

app.clientside_callback(
    """
    function(disable, location_types){
        
            if(disable === false){
                view_options = location_types;
            }
            else{
                view_options = [];
            }
            options = [];
            for(var i =0; i<view_options.length;i++){
                options.push({"label":view_options[i].charAt(0).toUpperCase() + view_options[i].slice(1), "value":view_options[i]})
            } 
            return (options)
    }
    """,
    Output(component_id="view_level", component_property="options"),
        # Output(component_id="view_level", component_property="disabled"),
        # Input(component_id="filter_dict", component_property="data"),
        [Input(component_id="view_level", component_property="disabled"),
        Input(component_id="location_types", component_property="data")]
)


# ====================Map Logic===================================#
# callback 7
@app.callback(
        Output(component_id="choropleth-container", component_property="children"),
    [
        Input(component_id="va_data", component_property="data"),
        Input(component_id="timeframe", component_property="value"),
        Input(component_id="cod_type", component_property="value"),
        Input(component_id="view_level", component_property="value"),
        Input(component_id="location_types", component_property="data"),
        Input(component_id="filter_dict", component_property="data"),
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
    **kwargs
):
    START_TIME = time.time()
    # first, see which input triggered update. If granularity change, log the new value
    context = dash.callback_context
    trigger = context.triggered[0]
    if trigger["prop_id"].split(".")[0] == "view_level":
        log_callback_trigger(LOGGER, dash.callback_context, kwargs["request"])
        
    figure = go.Figure()
    config = None

    if va_data is not None:
        # initialize variables
        all_data = pd.DataFrame(va_data)
        plot_data = all_data.copy()
        return_value = html.Div(id="choropleth")
        granularity = INITIAL_GRANULARITY
        location_types = location_types
        include_no_datas = True
        ret_val = dict()
        border_thickness = 0.25  # thickness of borders on map
        # name of column to plot
        data_value = (
            "age_mean" if len(re.findall("[mM]ean", cod_type)) > 0 else "id_count"
        )

        if plot_data.size > 0:
            timeframe = timeframe.lower()
            feature_id = "properties.area_name"
            plot_geos = geojson["features"]

            # if dashboard filter applied, carry over to data
            if filter_dict is not None:
                granularity = filter_dict.get("granularity", granularity)

                # geo_filter is true if user clicked on map or searches for location
                zoom_in = filter_dict["geo_filter"]
                plot_regions = filter_dict["plot_regions"]
                
                # filter geojson to match plotting regions, stop update if regions are empty, No Data 
                if len(plot_regions) == 0 and zoom_in:
                    raise dash.exceptions.PreventUpdate
                
                plot_data = plot_data.loc[filter_dict["ids"]["valid"], :]
                # only proceed with filter if remaining data after filter
                if plot_data.size > 0:
                    # if zoom in necessary, filter geojson to only chosen region(s)
                    if zoom_in:
                        # if user has clicked on map, try to zoom into a finer granularity
                        granularity = shift_granularity(
                            granularity, location_types, move_up=False
                        )

                        plot_geos = [
                            g for g in geojson["features"]
                            if g["properties"]["area_name"] in plot_regions
                        ]
                        chosen_region = plot_data[granularity].unique()[0]

                        # if adjacent_ids specified, and data exists for these regions, plot them on map first
                        plot_ids = filter_dict["plot_ids"]["valid"]

                        if len(plot_ids) > 0:
                            adjacent_data = all_data.loc[plot_ids, :].loc[
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

            # handle the case where there's no va records
            if plot_data.size == 0:
                # display no datas if the data is empty
                include_no_datas = True
            # if user has not chosen a view level or user is zooming in, default to granularity
            view_level = granularity if len(view_level) == 0 or zoom_in else view_level
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
            # set a fixed scale for zero data
            if plot_data.size == 0:
                figure.update_traces(
                    zmin=0,
                    zmax=8,
                )
            # additional styling
            config = LOOKUP['graph_config']
            # if geo restrictions in place, disable clicking
            if kwargs["user"].location_restrictions.exists():
                config["scrollZoom"] = False
                config["showAxisDragHandles"] = False
                    
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
    
    return_value = dcc.Graph(id="choropleth", figure=figure, config=config)
    print("update choropleth Callback", time.time() - START_TIME)
    return return_value#, json.dumps(ret_val)


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

    # doesn't matter if map data is empty if we join with empty data
    if va_df.size > 0 or include_no_datas:
        map_df = (
            va_df[[view_level, "id", "age", "location"]]
            .groupby(view_level)
            .agg({"id": ["count"], "age": ["mean"], "location": [pd.Series.nunique]})
        )

        map_df.columns = ["_".join(tup) for tup in map_df.columns.to_flat_index()]
        map_df.reset_index(inplace=True)

        # generate tooltips for regions with data
        metric_name = LOOKUP["display_names"].get(metric, metric)
        map_df["age_mean"] = np.round(map_df["age_mean"], 1)
        map_df["tooltip"] = (
            "<b>"
            + map_df[view_level]
            + "</b>"
            + "<br>"
            + f"<b>{metric_name}: </b>"
            + map_df["id_count"].astype(str)
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
# callback 8
@app.callback(
    Output(component_id="callout-container", component_property="children"),
    [
        Input(component_id="va_data", component_property="data"),
        Input(component_id="invalid_va_data", component_property="data"),
        Input(component_id="timeframe", component_property="value"),
        Input(component_id="filter_dict", component_property="data"),
    ],
)
def update_callouts(
    va_data, invalid_va_data, timeframe, filter_dict=None, geojson=GEOJSON, **kwargs
):
    START_TIME = time.time()
    coded_vas, uncoded_vas, active_facilities, num_field_workers, coverage = (
        0,
        0,
        0,
        0,
        0,
    )
    if va_data is not None:
        plot_data = pd.DataFrame(va_data)
        invalid_va_data = pd.DataFrame(invalid_va_data)
        granularity = INITIAL_GRANULARITY
        if plot_data.size > 0:
            if filter_dict is not None:
                plot_data = plot_data.loc[filter_dict["ids"]["valid"], :]
                invalid_va_data = invalid_va_data.loc[filter_dict["ids"]["invalid"], :]
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
    print("callouts Callback", time.time() - START_TIME)
    return [
        make_card(coded_vas, header="Coded VAs", tooltip="# of VAs with COD assignments in chosen region and time period"),
        make_card(uncoded_vas, header="Uncoded VAs", tooltip="# of VAs in system missing COD assignments in chosen region and time period"),
        make_card(active_facilities, header="Active Facilities", tooltip="# of facilities that have submitted VAs in chosen region and time period"),
        # TODO: uncomment this once field worker calculation is possible
        # make_card(num_field_workers, header="Field Workers", tooltip="# of Field Workers that have submitted VAs in chosen region and time period"),
        make_card(coverage, header="Region Representation", tooltip="% of region type with data within surrounding geography type - ie. Facilities reporting data within District", style={"width": "225px"}),
    ]


### Client-side conversion attempt for update_callouts ###
# app.clientside_callback(
#     """
#     function(
#         va_data, invalid_va_data, timeframe, filter_dict, geojson, granularity
#     ){
#         var coded_vas = 0;
#         var uncoded_vas = 0;
#         var active_facilities = 0;
#         var num_field_workers = 0;
#         var coverage = 0;
#         //console.log(va_data);
#         if (va_data){
#             // plot_data = pd.DataFrame(va_data)
#             plot_data = va_data
#             // invalid_va_data = pd.DataFrame(invalid_va_data)
#             invalid_va_data = invalid_va_data
#             granularity = granularity['granularity'] // INITIAL_GRANULARITY
#             //if (plot_data.size > 0){
#             if(true){
#                 if (filter_dict){
#                     // plot_data = plot_data.loc[filter_dict["ids"]["valid"], ]
#                     plot_data = plot_data;
#                     // invalid_va_data = invalid_va_data.loc[filter_dict["ids"]["invalid"], ]
#                     invalid_va_data = invalid_va_data;
#                     // granularity = filter_dict.get("granularity", granularity)
#                     if(Object.keys(filter_dict).includes("granularity")){
#                         granularity = filter_dict['granularity']
#                     }
#                 }

#                 //# total valid (coded) VAs
#                 // coded_vas = plot_data.shape[0]
#                 //console.log(plot_data['id']);
#                 var filtered_ids = new Map(Object.entries(plot_data['id']))
#                 var coded_vas = _.filter([...filtered_ids].map(([name, value]) => ({ name, value })), function(o) {return filter_dict['ids']['valid'].includes(o.name);});
#                 //console.log("coded_vas");
#                 //console.log(coded_vas);
#                 coded_vas = Object.values(coded_vas).length
#                 // coded_vas = plot_data.length 
#                 //console.log("PLOT DATA LENGTH")
#                 //console.log(plot_data.length)

#                 //# total invalid (uncoded) VAs
#                 // uncoded_vas = invalid_va_data.shape[0]
#                 // uncoded_vas = invalid_va_data.length
#                 var uncoded_vas = _.filter([...filtered_ids].map(([name, value]) => ({ name, value })), function(o) {return filter_dict['ids']['invalid'].includes(o.name);});
#                 uncoded_vas = Object.values(uncoded_vas).length

#                 //# active facilities
#                 //console.log("PLOT DATA LOCATION");
#                 //console.log(plot_data['location']);
#                 //console.log("UNIQUE");
#                 //console.log("plot-data locs");
#                 //console.log(plot_data['location']);
#                 var filtered_locs= new Map(Object.entries(plot_data['location']))
#                 //console.log("FILTERED LOCS");
#                 //console.log([...filtered_locs]);
#                 filtered_locs = _.filter([...filtered_locs].map(([name, value]) => ({ name, value })), function(o) {return filter_dict['ids']['valid'].includes(o.name);})
#                 //console.log(_.uniq(Object.values(filtered_locs)));
                
#                 active_facilities = _.uniq(Object.values(plot_data['location'])).length
#                 active_faciliites = _.uniq(Object.values(filtered_locs)).length
#                 // active_facilities = plot_data["location"].nunique()

#                 //# TODO: get field worker data from ODK - this is just a janky hack
#                 // num_field_workers = int(1.25 * active_facilities)
#                 num_field_workers = Math.floor(1.25 * active_facilities)

#                 //# region 'representation' (fraction of chosen regions that have VAs)
#                 // total_regions = geojson[f"{granularity}_count"]
#                 total_regions = geojson[granularity + "_count"]

#                 if (filter_dict){
#                     if (filter_dict["plot_regions"].length > 0){
#                         total_regions = filter_dict["plot_regions"].length

#                         //# TODO: fix this to be more generic
#                         if (granularity == "province"){
#                             granularity = "district"
#                         }
#                     }
#                 }
                
#                 //plot_data[[granularity, "age"]].dropna()[granularity].nunique()
#                 age = new Map(Object.entries(plot_data['age']))
#                 filtered = _.filter([...age].map(([name, value]) => ({ name, value })), function(o) {return o.value != undefined;})
#                 valid_age_ind = Object.keys(filtered);

#                 gran = new Map(Object.entries(plot_data[granularity]))
#                 filtered = _.filter([...gran].map(([name, value]) => ({ name, value })), function(o) {return (filter_dict['ids']['valid'].includes(o.name)) && (o.value != undefined) && (valid_age_ind.includes(o.name))})
#                 //console.log("FILTERED VALUES")
#                 //console.log(filtered);
#                 //console.log(Object.entries(filtered))
#                 filtered_uni = _.countBy(filtered, (rec) => {return rec.value});
#                 regions_covered = Object.keys(filtered_uni).length
#                 //console.log("REGIONS COVERED")
#                 //console.log(regions_covered)

#                 // _.without( [list of stuff], undefined) .. removes anything that is
#                 // OR _.compact() ...removes false, null, 0, "", undefined
#                 // _.uniq().length

#                 // coverage = "{}%".format(np.round(100 * regions_covered / total_regions, 0))
#                 coverage = (100 * regions_covered / total_regions).toFixed(2) + "%"
#             }
#         }
#         //console.log(coded_vas);
#         //console.log(uncoded_vas);
#         //console.log(active_facilities);
#         //console.log(coverage);
#         return [
#             coded_vas,
#             uncoded_vas,
#             active_facilities, 
#             // num_field_workers,
#             coverage, 
#         ]
        
#     }

#     """,
#     Output(component_id="callout-container-data", component_property="data"),
#     [
#         Input(component_id="va_data", component_property="data"),
#         Input(component_id="invalid_va_data", component_property="data"),
#         Input(component_id="timeframe", component_property="value"),
#         Input(component_id="filter_dict", component_property="data"),
#         Input(component_id="geojson_data", component_property="data"),
#         Input(component_id="granularity", component_property="data")
#     ]
# )



# @app.callback(
#     Output(component_id="callout-container", component_property="children"),
#     [
#         Input(component_id="callout-container-data", component_property="data"),
#     ],
# )
# def update_callouts(
#     data_data, geojson=GEOJSON, **kwargs
# ):
#     return [
#         make_card(data_data[0], header="Coded VAs", tooltip="# of VAs with COD assignments in chosen region and time period"),
#         make_card(data_data[1], header="Uncoded VAs", tooltip="# of VAs in system missing COD assignments in chosen region and time period"),
#         make_card(data_data[2], header="Active Facilities", tooltip="# of facilities that have submitted VAs in chosen region and time period"),
#         # TODO: uncomment this once field worker calculation is possible
#         # make_card(num_field_workers, header="Field Workers", tooltip="# of Field Workers that have submitted VAs in chosen region and time period"),
#         make_card(data_data[3], header="Region Representation", tooltip="% of region type with data within surrounding geography type - ie. Facilities reporting data within District", style={"width": "225px"}),
#     ]
### END client-side conversion attempt for update_callouts ###

# build a calloutbox with specific value
# colors: primary, secondary, info, success, warning, danger, light, dark
def make_card(
    value, header=None, description="", tooltip="", color="light", inverse=False, style=None
):
    card_content = []
    if header is not None:
        card_id = header.replace(" ", "")
        card_content.append(dbc.CardHeader([
            header,
            html.Span(
                html.Span(className="fas fa-info-circle"),
                style={"margin-left": "5px", "color": "rgba(75,75,75,0.5)"},
                id=f"{card_id}-tooltip-target"
            ),
            dbc.Tooltip(
                tooltip,
                target=f"{card_id}-tooltip-target",
            ),
        ], style={"padding": ".5rem"}))
    body = dbc.CardBody(
        [
            html.H3(value, className="card-title"),
            html.P(description, className="card-text",),
        ],
        style={"padding": ".5rem"},
    )
    card_content.append(body)
    if style is None:
        style = {"width": "185px"}
    card_obj = dbc.Card(card_content, color=color, inverse=inverse, className="mr-2")
    card_container = html.Div(card_obj, style=style)
    return card_container


# =========Demographic plot logic==============================================#
# callback 9
@app.callback(
    Output(component_id="demos-container", component_property="children"),
    [
        Input(component_id="va_data", component_property="data"),
        Input(component_id="timeframe", component_property="value"),
        Input(component_id="filter_dict", component_property="data"),
    ],
)
def demographic_plot(va_data, timeframe, filter_dict=None, **kwargs):
    START_TIME = time.time()
    figure = go.Figure()
    if va_data is not None:
        plot_data = pd.DataFrame(va_data)
        if plot_data.size > 0:
            if filter_dict is not None:
                plot_data = plot_data.loc[filter_dict["ids"]["valid"], :]
                # if cod chosen, filter down to only vas with chosen cod
                if filter_dict["cod_type"].lower() != "all":
                    cod = filter_dict["cod_type"]
                    plot_data = plot_data[plot_data["cause"] == cod]
                    cod_title = LOOKUP["display_names"].get(cod, cod)
                    plot_title = f"{cod_title} Demographics"
                else:
                    plot_title = "All-Cause Demographics"
            figure = plotting.demographic_plot(plot_data, title=plot_title)
            log_callback_trigger(LOGGER, dash.callback_context, kwargs["request"])
    print("Demographics plot Callback", time.time() - START_TIME)
    return dcc.Graph(id="demos_plot", figure=figure, config=LOOKUP["chart_config"])

# =========Cause of Death Plot Logic============================================#
# callback 10
@app.callback(
    Output(component_id="cod-container", component_property="children"),
    [
        Input(component_id="va_data", component_property="data"),
        Input(component_id="timeframe", component_property="value"),
        Input(component_id="cod_factor", component_property="value"),
        Input(component_id="cod_group", component_property="value"),
        Input(component_id="cod_n", component_property="value"),
        Input(component_id="filter_dict", component_property="data"),
    ],
)

def cod_plot(va_data, timeframe, factor="Overall", cod_groups="All CODs", N=10, filter_dict=None, **kwargs):
    START_TIME = time.time()
    figure = go.Figure()
    if len(cod_groups) > 0:
        if va_data is not None:
            plot_data = pd.DataFrame(va_data)
            if filter_dict is not None:
                cod = filter_dict["cod_type"]
                plot_data = plot_data.loc[filter_dict["ids"]["valid"], :]
            
                # if no cod group filter (default), call standard cod plotting function
            cod_groups = [cod_groups] if type(cod_groups) is str else cod_groups
            figure = plotting.cod_group_plot(
                plot_data, cod_groups, demographic=factor, N=N, chosen_cod=cod, height=560
            )
            log_callback_trigger(LOGGER, dash.callback_context, kwargs["request"])
        print("COD Plot Callback", time.time() - START_TIME)
        return dcc.Graph(id="cod_plot", figure=figure, config=LOOKUP["chart_config"])
    else:
        raise dash.exceptions.PreventUpdate     

# ========= Time Series Plot Logic============================================#
# callback 11
@app.callback(
    
     Output(component_id="ts-container", component_property="children"),
     

    
    [
        Input(component_id="va_data", component_property="data"),
        Input(component_id="timeframe", component_property="value"),
        Input(component_id="group_period", component_property="value"),
        Input(component_id="filter_dict", component_property="data"),
        Input(component_id="ts_factor", component_property="value"),
        Input(component_id="ts_search", component_property="value")
    ],
)
def trend_plot(va_data, timeframe, group_period, filter_dict=None, factor="All", search_terms=None, **kwargs):
    START_TIME = time.time()
    figure, plot_title = go.Figure(), None
    search_term_ids = {}
    if va_data is not None:
        plot_data = pd.DataFrame(va_data)
        if plot_data.size > 0:
            if filter_dict is not None:
                cod = filter_dict["cod_type"]
                plot_data = plot_data.loc[filter_dict["ids"]["valid"], :]
                # first, check for search terms. If any, use as filter
                search_terms= [] if search_terms == "All causes.all" else search_terms
                if search_terms and len(search_terms) > 0:
                    if type(search_terms) is str:
                        search_terms = [search_terms]
                    cod_groups = COD_GROUPS
                   
                    for search_value in search_terms:
                        if search_value.lower().startswith("all"):
                            search_value = "All causes.all"
                        # search term convention: {kewyword.type}
                        key, key_type = search_value.split(".")
                        # if keyword is a cod group, filter to only CODs in that group and only vas meeting that group's criteria
                        if key_type == "group":
                            # get ids of VAs meeting group criteria (e.g. if Neonate, subset to VAs with age < 1)
                            criteria_ids = plotting.cod_group_data(plot_data, key, cod_groups=cod_groups).index
                            # get ids of VAs meeting cod criteria (i.e. VAs with Neonatal CODs)
                            group_cods = cod_groups[cod_groups[key]==1]["cod"].tolist()
                            cod_ids = plot_data[plot_data["cause"].isin(group_cods)].index
                            # take intersection of criteria and cod ids to get final matching list
                            match_ids = criteria_ids.intersection(cod_ids).tolist()
                            
                        elif key_type == "cod":
                            match_ids = plot_data[plot_data["cause"] == key].index.tolist()
                        elif key_type == "all":
                            match_ids = plot_data.index.tolist()
                        search_term_ids[search_value] = match_ids
                    
                    # TODO: make this more generic (only assumes one search term)
                    search_key = search_terms[0].split('.')[0]
                    term_title = LOOKUP["display_names"].get(search_key,\
                                       search_key.capitalize())
                    plot_title = f"{term_title} Trend by {group_period}"
                # otherwise, check if global cod has been chosen   
                elif cod.lower() != "all":
                    cod_title = LOOKUP["display_names"].get(cod, cod)
                    plot_data = plot_data.loc[filter_dict["ids"]["valid"], :]
                    search_term_ids[cod] = plot_data[plot_data["cause"] == cod].index.tolist()
                    plot_title = f"{cod_title} Trend by {group_period}"
                    
            log_callback_trigger(LOGGER, dash.callback_context, kwargs["request"])

            figure = plotting.va_trend_plot(
                plot_data, group_period, factor, title=plot_title, search_term_ids=search_term_ids, height=560
            )
            # print("TIMEEEEEEEEEEEEEEEEEEE")
            # print(time.time() - START_TIME)
    print("trend plot Callback", time.time() - START_TIME)
    return dcc.Graph(id="trend_plot", figure=figure, config=LOOKUP["chart_config"])

# uncomment this if running as Dash app (as opposed to DjangoDash app)
# app.run_server(debug= True)