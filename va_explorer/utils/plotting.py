#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Feb 10 23:56:26 2021

@author: babraham
"""
import pandas as pd
import plotly.graph_objs as go
import plotly.figure_factory as ff
import plotly.express as px
import numpy as np
from plotly.subplots import make_subplots

D3 = px.colors.qualitative.D3
PLOTLY = px.colors.qualitative.Plotly
DEMO_LOOKUP = {"age group": "age_group",
                "sex": "Id10019",
                "place of death": "Id10058"
}

DEATH_LOCATIONS = {
    "on_route_to_hospital_or_facility": "En Route to Facility",
    "DK": "Unknown",
    "other_health_facility": "Other Health Facility",
}  

# get counts by age group
def get_age_plot_data(va_df, age_col=None):
    if not age_col:
        age_col = DEMO_LOOKUP["age group"]
    return (va_df[age_col].value_counts()
          .reset_index()
          .rename(columns={'age_group': 'count', 'index': 'age_group'})
          .assign(age_group = lambda df: df['age_group'].str.capitalize(), 
                  percent = lambda df: df.apply(lambda x: np.round(100*x['count']/df['count'].sum(),1), axis=1))
          .assign(label = lambda df: df['count'].astype(str) + '<br> (' + df['percent'].astype(str) + '%)')

         )
          
# get va counts by gender
def get_gender_plot_data(va_df, gender_col=None):
    if not gender_col:
        gender_col = DEMO_LOOKUP["sex"]
    return (va_df[gender_col].value_counts()
          .reset_index()
          .rename(columns={'index': 'gender', gender_col: 'count'})
          .assign(gender = lambda df: df['gender'].str.capitalize(), 
                  percent = lambda df: np.round(100*df['count']/df['count'].sum(), 2))
          .assign(label = lambda df:  df['count'].astype(str) + '<br> (' + df['percent'].astype(str) + '%)')
    )
          
# get va counts by place of death
def get_place_of_death_plot_data(va_df, place_of_death_col=None):
    if not place_of_death_col:
        place_of_death_col = DEMO_LOOKUP["place of death"]
    return (va_df[place_of_death_col]
        .value_counts()
        .reset_index()
        .rename(columns={'index': 'location', place_of_death_col:'count'})
        .assign(percent = lambda df: np.round(100*df['count']/df['count'].sum(), 2), 
                location = lambda df: df['location'].apply(lambda x: DEATH_LOCATIONS.get(x,x.capitalize())))
        .assign(label = lambda df: df['count'].astype(str) + ' (' + df['percent'].astype(str) + '%)')
    )


# create a multiplot of va counts by gender, age, and place of death
def demographic_plot(va_df, column_widths=None, height=600):
    if not column_widths:
        first_width = .4
        column_widths = [first_width, 1 - first_width]
    comb_fig = make_subplots(
        rows=2, cols=2,
        specs=[[{'type': 'bar'}, {'type': 'bar'}],
               [{"colspan": 2}, None]],
        subplot_titles=("Gender","Age Group", "Place of Death"), 
        column_widths=column_widths)

    # gender
    sex_df = get_gender_plot_data(va_df)
    comb_fig.add_trace(go.Bar(x=sex_df['gender'], y=sex_df['count'], text=sex_df['label'], textposition='auto',
               showlegend=False, marker_color = PLOTLY),
        row=1, col=1)

    # age groups
    age_df = get_age_plot_data(va_df)
    comb_fig.add_trace(
        go.Bar(x=age_df['age_group'], y=age_df['count'], text=age_df['label'], textposition='auto',
               showlegend=False, marker_color = D3),
        row=1, col=2)

    # place of death
    loc_cts = get_place_of_death_plot_data(va_df)
    comb_fig.add_trace(
        go.Bar(name='Place of Death', 
               x=loc_cts['count'], y=loc_cts['location'], orientation='h', showlegend=False,
               text=loc_cts['label'],
            textposition="auto", marker_color=PLOTLY[3:]),
        row=2, col=1
    )
    return comb_fig.update_layout(height=height)