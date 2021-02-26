#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Feb 19 10:46:16 2021

@author: babraham
"""
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc

TABS = {}

def get_first_tab_key(tab_dict):
    keys = [k for k in tab_dict.keys()]
    if len(keys) > 0:
        return keys[0]
    
# graph tabs
#=============COD tab====================#
cod_key = 'cod_tab'

TABS[cod_key] = dcc.Tab(
    value=cod_key,
    id='cod_tab_id',
    label="COD Comparison",
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
                                    "value": o.lower(),
                                }
                                for o in [
                                    "All",
                                    "Age Group",
                                    "Sex",
                                    "Place of Death"
                                ]
                            ],
                            value="all",
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
                                for o in [5,10,15,20]
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
                )
            ],
            style={
                "display": "flex",
                "align-items": "center",
            },
        ),
        dcc.Loading(html.Div(id="cod-container"), type='circle'),
    ],
    disabled=False
)
#==========Demographics Tab===================#
demo_key = 'demographic_tab'
TABS[demo_key] = dcc.Tab(
    value=demo_key,
    label="Demographics",
    children=[dcc.Loading(html.Div(id="demos-container"), type='circle')]
)
#==========VA Trends Tab=====================#
trend_key = 'va_trend_tab'
TABS[trend_key] = dcc.Tab(
    value=trend_key,
    label="VA Trends",
    children=[
        html.Div(
            id="ts_buttons",
            children=[
                html.Div(
                    [
                        html.P(
                            "Frequency",
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
                                {"label": o, "value": o}
                                for o in ["All","Age Group","Sex","Place of Death"]
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
    )
                        
# render blank tabs
BLANK_TABS = [dcc.Tab(value=k, label=tab.label) for k, tab in TABS.items()]