#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Feb 10 23:56:26 2021

@author: babraham
"""
import os

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objs as go
from plotly.subplots import make_subplots

# ===========PLOTTING PROPERTIES/VARIABLES=====================#
D3 = px.colors.qualitative.D3
PLOTLY = px.colors.qualitative.Plotly


# plotting properties defined below
# ======= PLOTTING PROPERTIES ==============#
def load_lookup_dicts():
    lookup = dict()
    # dictionary mapping time labels to days (or all)
    lookup["time_dict"] = {"today": 1, 
                          "last week": 7,
                          "last month": 30,
                          "last 3 months": 30.4 * 3,
                          "last 6 months": 30.4 * 6, # last 182.5 days
                          "last year": 365,
                          # assuming all VAs occured in last 30 years
                          "all": "all"} 
    # dictionary mapping demographic variable names to corresponding VA survey columns
    lookup["demo_to_col"] = {
        "age group": "age_group",
        "sex": "Id10019",
        "place of death": "Id10058",
    }
    # colors used for plotting - override with whatever color scheme you'd like
    lookup["color_list"] = [
        "rgb(24,162,185)", # turquoise
        "rgb(201,0,1)", # burgandy
        "rgb(8,201,0)", #  green
        "rgb(240,205,21)", # gold
        "rgb(187,21,240)", # purple
        "rgb(162,162,162)", # gray
        "rgb(239,86,59)", # dark orange
        "rgb(20,72,123)", # midnight blue, 
        "rgb(9,112,13)", # dark green
        "rgb(239,49,255)" # fuschia
    ]
    # colorscale used for map
    lookup["colorscales"] = {
        "primary": [
            (0.0, "rgb(255,255,255)"),
            (1e-20, "rgb(0, 147, 146)"),
            (0.167, "rgb(0, 147, 146)"),
            (0.167, "rgb(57, 177, 133)"),
            (0.333, "rgb(57, 177, 133)"),
            (0.333, "rgb(156, 203, 134)"),
            (0.5, "rgb(156, 203, 134)"),
            (0.5, "rgb(233, 226, 156)"),
            (0.667, "rgb(233, 226, 156)"),
            (0.667, "rgb(238, 180, 121)"),
            (0.833, "rgb(238, 180, 121)"),
            (0.833, "rgb(232, 132, 113)"),
            (1.0, "rgb(232, 132, 113)"),
        ],
        "secondary": [
            (0.0, "rgb(255,255,255)"),
            (0.001, "rgb(230,230,230)"),
            (1.0, "rgb(230,230,230)"),
        ],
    }

    lookup["line_colors"] = {"primary": "black", "secondary": "gray"}
    # dictionary mapping certain concepts to display names
    lookup["display_names"] = {
        # Internal CODs to human-readable titles
        "all": "All Causes",
        "Coded VAs": "Coded VAs",
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
        "Other and unspecified infect dis": "Other infectious disease",
        "Other and unspecified maternal CoD": "Other maternal CoD",
        "Pregnancy-induced hypertension": "Hypertension from Pregnancy",

        # internal cod group labels to plot titles
        "All CODs": "All Causes",
        "ncd": "Non-Communicable",
        "parasitic": "Parasitic",
        "infectious": "Infectious", 
        "zambia_notifiable_disease": "Zambian Notifiable",
        "respiratory": "Respiratory",

        # place of death names to more human-readable names
        "on_route_to_hospital_or_facility": "En Route to Facility",
        "dk": "Unknown",
        "other_health_facility": "Other Health Facility",
        "ref": "Refused to Answer"
    }
    # formats for montly, weekly, and yearly dates
    lookup["date_display_formats"] = {
        "week": "%d/%m/%Y",
        "month": "%m/%Y",
        "year": "%Y",
    }
    
    # Toolbar configurations for plots
    # map config
    lookup['graph_config'] = {"displayModeBar": True,
          "scrollZoom": True, "displaylogo": False,
          "modeBarButtonsToRemove":["zoomInGeo", "zoomOutGeo", "select2d", "lasso2d"]}
    # chart config (for all charts)
    lookup['chart_config'] = {"displayModeBar": True,
          "displaylogo":False,
          "modeBarButtonsToRemove":["pan2d", "zoom2d", "select2d", \
                        "lasso2d", "zoomIn2d", "zoomOut2d", "autoScale2d", "resetScale2d"]}

    return lookup


LOOKUP = load_lookup_dicts()


# get counts of a categorical field from va data. Field name can either be a
# column name in the dataframe or a demographic lookup key. Change final column name with display_name argument.
def get_field_counts(va_df, field_name, full_labels=False, display_name=None):
    if field_name not in va_df.columns:
        # if no matching column in va_df for field name, try lookup in the demo_to_col dict.
        if not display_name:
            # if no display name provided, use original key
            display_name = field_name
        field_name = LOOKUP["demo_to_col"].get(field_name, field_name)
    assert field_name in va_df.columns

    va_df = (
        va_df[field_name]
        .value_counts()
        .reset_index()
        .assign(index=lambda df: df["index"].str.capitalize())
        .rename(columns={field_name: "count", "index": "group"})
        .assign(
            percent=lambda df: df.apply(
                lambda x: np.round(100 * x["count"] / df["count"].sum(), 1), axis=1
            )
        )
        .assign(label=lambda df: df["percent"].astype(str) + "%")
    )
    if display_name:
        va_df = va_df.rename(columns={"group": display_name})

    if full_labels:
        va_df["label"] = (
            va_df["count"].astype(str) + "<br> (" + va_df["percent"].astype(str) + "%)"
        )

    return va_df


# ===========DEMOGRAPHIC PLOT LOGIC=========================#
# create a multiplot of va counts by gender, age, and place of death
def demographic_plot(va_df, no_grids=True, column_widths=None, height=600, title=None):
    if not column_widths:
        first_width = 0.4
        column_widths = [first_width, 1 - first_width]
    comb_fig = make_subplots(
        rows=2,
        cols=2,
        specs=[[{"type": "bar"}, {"type": "bar"}], [{"colspan": 2}, None]],
        subplot_titles=("Gender", "Age Group", "Place of Death"),
        column_widths=column_widths,
        vertical_spacing=0.15,
    )

    if va_df.size > 0:
        # gender
        sex_df = get_field_counts(va_df, "sex", display_name="gender")
        comb_fig.add_trace(
            go.Bar(
                name="Gender",
                x=sex_df["gender"],
                y=sex_df["count"],
                text=sex_df["label"],
                textposition="auto",
                showlegend=False,
                marker_color=PLOTLY,
            ),
            row=1,
            col=1,
        )

        # age groups
        age_df = get_field_counts(va_df, "age group", display_name="age_group")
        comb_fig.add_trace(
            go.Bar(
               name="Age Group",
                x=age_df["age_group"],
                y=age_df["count"],
                text=age_df["label"],
                textposition="auto",
                showlegend=False,
                marker_color=D3,
            ),
            row=1,
            col=2,
        )

        # place of death
        loc_cts = get_field_counts(va_df, "place of death", display_name="location")
        loc_cts["location"] = loc_cts["location"].apply(
            lambda x: LOOKUP["display_names"].get(x.lower(), x.capitalize())
        )
        comb_fig.add_trace(
            go.Bar(
                name="Place of Death",
                x=loc_cts["count"],
                y=loc_cts["location"],
                orientation="h",
                showlegend=False,
                text=loc_cts["label"],
                textposition="auto",
                marker_color=D3[4],
            ),
            row=2,
            col=1,
        )
    else:
        title = "No Data for Selected Criteria"
        no_grids = False
        gender_labels, gender_counts = [''], [0]
        comb_fig.add_trace(
            go.Bar(
                name="Gender",
                x=gender_labels,
                y=gender_counts,
                textposition="auto",
                showlegend=False,
            ),
        )

        age_labels, age_counts = [''], [0]
        comb_fig.add_trace(
            go.Bar(
                name="Age Group",
                x=age_labels,
                y=age_counts,
                #text=age_labels,
                #textposition="auto",
                showlegend=False,
                marker_color=D3,
            ),
            row=1, col=2,
        )
        place_labels, place_counts = [''], [0]
        comb_fig.add_trace(
            go.Bar(
                name="Place of Death",  
                x=place_counts,
                y=place_labels,
                orientation="h",
                showlegend=False,
            ),
            row=2,col=1,
        )
        comb_fig.update_xaxes(range=[0,1])
        comb_fig.update_yaxes(range=[0,1])

    if no_grids:
        comb_fig.update_xaxes(showgrid=False)
        comb_fig.update_yaxes(showgrid=False)

    if title:
        comb_fig.update_layout(title_text=title)

    return comb_fig.update_layout(height=height)


# ===========CAUSE OF DEATH PLOTTING LOGIC=========================#

# function to load cod groupings csv file used for cod group plotting. 
# each cod is a row, and each column is a possible group. 
    
def load_cod_groupings(data_dir=None, grouping_file="cod_groupings.csv"):
    group_data = pd.DataFrame()
    
    if not data_dir:
        data_dir = "va_explorer/va_analytics/dash_apps/dashboard_data" 
        
    if not grouping_file.endswith(".csv"):
        raise AttributeError("Must provide grouping file in csv format")
    
    fname = f"{data_dir}/{grouping_file}"
    if os.path.isfile(fname):
        group_data = pd.read_csv(fname)
    else:
        print(f'WARNING: couldnt find {fname}' )
        
    return group_data

# get all vas with cods in a certain cod group
def cod_group_data(va_df, group, cod_groups=pd.DataFrame(), N=10):
    va_filtered = pd.DataFrame()
    if cod_groups.size == 0:
        data_dir = "va_explorer/va_analytics/dash_apps/dashboard_data" 
        cod_groups = pd.read_csv(f"{data_dir}/cod_groupings.csv")
    group = group.lower()
    if group == 'neonatal':
        age_col = 'ageInYears' if 'ageInYears' in va_df.columns else 'ageinyears'
        va_df[age_col] = va_df[age_col].astype(float, errors='ignore')
        # definition from 2016 WHO VA form
        va_filtered = va_df[va_df[age_col] < 1]
    else:

        # don't filter if group starts with 'all'
        if group.startswith('all'):
            top_cods = va_df['cause'].value_counts().sort_values(ascending=False).head(N).index
            va_filtered = va_df[va_df["cause"].isin(set(top_cods))]
        elif group in cod_groups.columns:
            cod_group = cod_groups.loc[cod_groups[group]==1, 'cod']
            va_filtered = va_df[va_df['cause'].isin(cod_group)]
    return va_filtered


# turn two columns from a va dataframe into a pivot table
def get_pivot_counts(va_df, index_col, factor_col):
    if factor_col.lower() in ['all', 'overall']:
        counts = va_df.groupby(index_col).count().iloc[:,[1]]
        counts.columns = ['overall']
    else:
        if factor_col not in va_df.columns:
            factor_col = LOOKUP["demo_to_col"][factor_col]
        assert factor_col in va_df.columns and index_col in va_df.columns
        counts = va_df.pivot_table(
            index=index_col,
            columns=factor_col,
            values="id",
            aggfunc=pd.Series.nunique,
            fill_value=0,
            margins=True,
        )
    return counts


def cod_group_plot(va_df, cod_groups=[], demographic="overall", N=10, height=None, vertical_spacing=.15,\
                   chosen_cod="all"):
    figure = go.Figure()
    # if no demographic chosen (i.e. overall), color-code by cause-of-death group. Otherwise, color-code by demographic
    demographic = demographic.lower()
    if demographic in ['overall', 'all']:
        color_keys = cod_groups
    else:
        demo_column = LOOKUP["demo_to_col"].get(demographic, demographic)
        color_keys = va_df[demo_column].unique().tolist()
    color_dict = {color_key: LOOKUP["color_list"][i] for i, color_key in enumerate(color_keys)}
    
    # build subplots incrementally and store them in a list of dictionaries
    subplots = []
    legend_names = set()
    if va_df.size > 0:

        # create 1 subplot per group and store data
        for i, cod_group in enumerate(cod_groups):
            
            # default values for group's height and traces. 
            group_height, group_traces = 1, []
            
            # filter va data down to only group of interest
            cod_data = cod_group_data(va_df, cod_group, N=N)
            
            # only proceed if any group data
            if cod_data.size > 0:
                # get demographic pivot and remove row total (not a COD)
                cod_pivot = get_pivot_counts(cod_data, "cause", demographic).query("cause != 'All'") 
                # get top N by total count (last column of pivot table) and flip order for plotting
                cod_pivot = cod_pivot.sort_values(by=cod_pivot.columns[-1], ascending=False).head(N).iloc[::-1]
                cod_pivot.index = [LOOKUP["display_names"].get(x,x) for x in cod_pivot.index]
                cod_pivot["cod"] = cod_pivot.index
                demo_groups = sorted(list(cod_pivot.columns.difference(['All', 'cod'])))
                # set relative group height to at most N
                group_height = cod_pivot.shape[0]
                if cod_group.lower().startswith("all"):
                    group_title = "Top CODs Overall"
                else:
                    group_title = group_title = "Top <b>{}</b> CODs".format(LOOKUP['display_names'].get(cod_group, cod_group.capitalize()))
                
                # make a subplot trace for each demographic
                for j, demo_group in enumerate(demo_groups):
                    if demographic not in ['overall', 'all']:
                        group_key = demo_group
                        
                        denominators = cod_pivot[demo_groups].sum(axis=1)
                    else:
                        group_key = cod_group
                        denominators = cod_pivot[demo_group].sum()
    
                    counts = cod_pivot.loc[cod_pivot[demo_group] > 0, ["cod", demo_group]]
                    counts = (counts[counts["cod"] != "All"])#.sort_values(by=demo_group, ascending=True))
                    
                    counts[f"{demo_group}_pct"] = np.round(100 * counts[demo_group] / denominators, 2)
                    counts["text"] = f"<i>{demo_group}</i><br>" +\
                                    counts[demo_group].astype(str) +\
                                    " (" + counts[f"{demo_group}_pct"].astype(str) + " %)"
                    
                    lines = [LOOKUP["line_colors"]["secondary"]] * counts.shape[0]
                    widths = np.repeat(1, len(counts['cod']))
                    
                    # if a specific cod is chosen from global dropdown, highlight it if present in group CODs
                    if chosen_cod != "all":
                        chosen_cod = LOOKUP["display_names"].get(chosen_cod, chosen_cod)
                        # only highlight if chosen_cod present
                        if chosen_cod in counts.index:
                            chosen_idx = counts.index.get_loc(chosen_cod)
                            lines[chosen_idx] = "#e0b816" 
                            widths[chosen_idx] = 3
                            counts["cod"][chosen_idx] = "<b>" + counts["cod"][chosen_idx] + "</b>"
                    
                    # create traces (for both counts and %s) and add it to group's traces
                    for k, trace_type in enumerate([demo_group, f"{demo_group}_pct"]):
                        show_legend = (group_key not in legend_names and k==0)
                        group_legend_name = LOOKUP["display_names"].get(group_key, group_key.capitalize())
                        trace = go.Bar(
                                    x=counts[trace_type],
                                    y=counts["cod"],
                                    text=counts["text"],
                                    name=group_legend_name,
                                    visible=(k==0), # only show counts first
                                    showlegend=show_legend,
                                    orientation="h",
                                    hovertemplate = "<b>%{y}</b> <br>%{text}<extra></extra>",
                                    marker=dict(
                                        color= color_dict[group_key],
                                        line=dict(color=lines, width=widths)
                                    ),
                                )
                        group_traces.insert(0, trace)
                        legend_names.add(group_key)
            else:
                group_title = f"No Observed <b>{cod_group.capitalize()}</b> CODs"
                    
            # store all data needed to create group subplot in a single dictionary
            subplot = {"group": cod_group, "title": group_title, "data": group_traces, "height": group_height}
            subplots.insert(0, subplot)
            
        # sort subplots by height (i.e. amount of data)
        subplots = sorted(subplots, key=lambda subplot: subplot["height"])
        
        ## Step 2: Combine info across groups to form plot layout, data, and annotation variables
        data, axes, title_annotations = [], {}, []
        y_min, y_max = 0,0
        total_height = sum(subplot["height"] for subplot in subplots)
        # total area to allocate for subplots, accounting for title spaces 
        total_available_area = 1 - vertical_spacing * len(subplots)
        for i, subplot in enumerate(subplots):
            # create axes
            axis_idx = "" if i == 0 else i+1
            xaxis_i = {"domain": [0,1], "anchor": f"y{axis_idx}"}
            subplot_height = total_available_area * subplot["height"] / total_height
            # update upper limit of y range to reflect subplot height
            y_max = np.round(y_max + subplot_height, 3)
            yaxis_i = {"domain": [y_min, y_max], "anchor": f"x{axis_idx}"}
            # add new axes to axes dict
            axes[f"xaxis{axis_idx}"] = xaxis_i
            axes[f"yaxis{axis_idx}"] = yaxis_i
    
            # add each trace to data list
            for trace in subplot["data"]:
                # add axes references to current trace
                trace["xaxis"] = f"x{axis_idx}"
                trace["yaxis"] = f"y{axis_idx}"
                data.insert(0, trace)
    
            # make annotation for group title and add to plot annotations
            title_annotation = {'text': subplot["title"], 'font': {'size': 16}, 'showarrow': False,
                             'x': 0.5, 'xref': 'paper','y': y_max, 'yanchor': 'bottom','yref': 'paper'}
            title_annotations.insert(0, title_annotation)
            # add spacing for title to y_max
            y_max += vertical_spacing 
            # move y_min forward for next plot
            y_min = y_max
        
        # create figure with necessary data and axes
        figure = go.Figure(data=data, layout=axes)
    
        # add titles and other finishing touches to plot
        figure.update_layout(annotations=title_annotations, 
                          barmode="stack",
                          height=height,
                          legend=dict(traceorder='normal', yanchor="top", y=1-vertical_spacing), 
                          margin={'t':30})
        # add count/percent buttons
        buttons = create_percent_count_buttons(num_groups=int(len(figure.data)/2), y=1, traces=figure.data)
        figure.update_layout(updatemenus=[buttons])
    else:
        figure.update_xaxes(range=[0,1])
        figure.update_yaxes(range=[0,1])
        figure.update_layout(title_text="No Data for Selected Criteria")
        
    return figure


# plot top N causes of death in va_data either overall or by factor/demographic
def cause_of_death_plot(va_df, factor, N=10, chosen_cod="all", title=None, height=None):
    
    figure, factor, factor_title = go.Figure(), factor.lower(), "Overall"
    
    if factor not in ["all", "overall"]:
        factor_title = "by " + factor.capitalize()
        
    plot_title = "Top Causes of Death {}".format(factor_title) if not title else title
    
    # get cause counts by chosen factor (by default, overall counts)
    counts = get_pivot_counts(va_df, "cause", factor).rename(columns={"overall": "All"})

    if va_df.size > 0:
        # make index labels pretty
        counts.index = [LOOKUP["display_names"].get(x, x) for x in counts.index]
        counts["cod"] = counts.index
        counts = (counts[counts["cod"] != "All"].sort_values(by="All", ascending=False).head(N))
        groups = list(set(counts.columns).difference(set(["cod"])))
        
        lines = [LOOKUP["line_colors"]["secondary"]] * counts.shape[0]
        widths = np.repeat(1, len(counts['cod']))
        if chosen_cod != "all":
            chosen_cod = LOOKUP["display_names"].get(chosen_cod, chosen_cod.capitalize())
            if chosen_cod in counts.index:
                chosen_idx = counts.index.get_loc(chosen_cod)
                lines[chosen_idx] = "#e0b816" 
                widths[chosen_idx] = 4
                counts["cod"][chosen_idx] = "<b>" + counts["cod"][chosen_idx] + "</b>"
    
        if factor not in ["all", "overall"]:
            groups.remove("All")
        for i, group in enumerate(groups):
            if factor in ["all", "overall"]: 
                # calculate percent as % of all cods (column-wise calculation)
                counts[f"{group}_pct"] = np.round(100 * counts[group] / counts[group].sum(), 1)
            else:
                # calculate percent as % across groups for specific cod (row-wise calculation)
                counts[f"{group}_pct"] = counts.apply(lambda row: np.round(100 * row[group] / row[groups].sum(), 1), axis=1)
            counts["text"] = f"<i>{group}</i><br>" + counts[group].astype(str) + " (" + counts[f"{group}_pct"].astype(str) + " %)"
            
            # add traces for counts and percents to enable toggling
            for j, trace_type in enumerate([group, f"{group}_pct"]):
                figure.add_trace(
                    go.Bar(
                        x=counts[trace_type],
                        y=counts["cod"],
                        text=counts["text"],
                        name=group.capitalize(),
                        orientation="h",
                        visible = (j==0),
                        hovertemplate = "<b>%{x}</b> <br>%{text}<extra></extra>",
                        marker=dict(
                            color= LOOKUP["color_list"][i],
                            line=dict(color=lines, width=widths),
                        ),
                    )
                )
        figure.update_layout(
            barmode="stack",
            title_text=plot_title,
            #xaxis_tickangle=-45,
            xaxis_title="Count",
            height=height,
            updatemenus=[
                    create_percent_count_buttons(num_groups=len(groups))
            ])
    else:
        cod_labels, cod_counts = [''], []
        # counts
        figure.add_trace(
            go.Bar(
                y=cod_counts,
                x=cod_labels,
                text=cod_labels,
                name="no data",
                orientation="v",
            )
        )
        figure.update_xaxes(range=[0,1])
        figure.update_yaxes(range=[0,1])
        figure.update_layout(
            barmode="stack",
            title_text="No Data for Selected Criteria",
            xaxis_tickangle=-45,
            yaxis_title="Count",
        )  
                    

        
    return figure


# create toggle to switch between counts and percents for barcharts
def create_percent_count_buttons(num_groups, x=1, y=1.2, traces=None):
    buttons = dict(
            type="buttons",
            direction="right",
            x=x, y=y,
            active=0,
            buttons=list([
                dict(label="Counts",
                     method="update",
                     args=[{"visible": [True, False] * num_groups}
                          ]),
                dict(label="Percents",
                     method="update",
                     args = [{"visible": [False, True] * num_groups},
                             ]),
  
            ]))
    # if traces provided, add logic to figure out which traces to show in legend when toggling between counts and percents
    if traces:
        # initial vector of which count traces to display in legend
        counts_show_legend = [trace.showlegend for trace in traces]
        # for percents, shift values one trace forward so percent equivalents are shown in legend
        percents_show_legend = counts_show_legend.copy()
        percents_show_legend.insert(0, False)
        percents_show_legend.pop(-1)
        # add showlegends argument to count button update function
        buttons['buttons'][0]['args'][0]["showlegend"] = counts_show_legend
        # add showlegends argument to count percent update function
        buttons['buttons'][1]['args'][0]["showlegend"] = percents_show_legend
    return buttons



# ========TREND/TIMESERIES PLOT LOGI======================#
def va_trend_plot(va_df, group_period, factor="All", title=None, search_term_ids=None, height=None):
    #figure = go.Figure()
    group_period = group_period.lower()
    aggregate_title = group_period.capitalize()
    factor = factor.lower()
    plot_fn = go.Scatter
    
    if va_df.size > 0:
        va_df["date"] = pd.to_datetime(va_df["date"])
        va_df["timegroup"] = pd.to_datetime(va_df["date"])
        if group_period == "week":
            va_df["timegroup"] = pd.to_datetime(
                va_df["date"].dt.to_period("W").apply(lambda x: x.strftime("%Y-%m-%d"))
            )
        elif group_period == "month":
            va_df["timegroup"] = pd.to_datetime(
                va_df["date"].dt.to_period("M").apply(lambda x: x.strftime("%Y-%m"))
            )
        elif group_period == "year":
            va_df["timegroup"] = va_df["date"].dt.to_period("Y").astype(str)
            
        if not search_term_ids:
            search_term_ids = {"All CODs": va_df.index.tolist()}
            
        # build and store traces for later
        subplots = []
        legend_names = set()
        for term, ids in search_term_ids.items():
            subplot_traces = []
            trace_df = va_df.loc[ids,:]
            # build pivot based on filtered data
            if factor not in ["all", "overall"]:
                assert factor in LOOKUP["demo_to_col"]
                factor_col = LOOKUP["demo_to_col"][factor]
                trend_counts = trace_df.pivot_table(
                    index="timegroup",
                    columns=factor_col,
                    values="id",
                    aggfunc=pd.Series.nunique,
                    fill_value=0,
                    margins=False,
                )
                
            else:
                trend_counts = (
                    trace_df[["timegroup", "id"]]
                    .groupby("timegroup")
                    .count()
                    .rename(columns={"id": "all"})
                )
            # iterate through groups and add their traces to the plot
            for i, demo_group in enumerate(trend_counts.columns.tolist()):
                demo_group_name = LOOKUP["display_names"].get(demo_group.lower(), demo_group.capitalize())
                show_legend = (demo_group not in ["all", "overall"]) and (demo_group_name not in legend_names)
                trace_data =  plot_fn(
                            y=trend_counts[demo_group],
                            x=trend_counts.index,
                            name=demo_group_name,
                            showlegend=show_legend,
                            marker=dict(
                                color=LOOKUP["color_list"][i],
                                line=dict(color=LOOKUP["color_list"][i], width=1),
                            ),
                        )
                subplot_traces.insert(0, trace_data)
                legend_names.add(demo_group_name)
            if "." in term:
                term_name, term_type = term.split(".")
            else:
                term_name, term_type = term, ""
                
            term_title = LOOKUP["display_names"].get(term_name, term_name.capitalize())
            if term_type == "group":
                term_title += " CODs"
            subplot_title = f"<b>{term_title}</b> by {aggregate_title}"
            subplot = {"group": term, "title": subplot_title, "data": subplot_traces}
            subplots.insert(0, subplot)
            
        # make figure with one subplot per search term
        figure = make_subplots(
            rows=len(search_term_ids.keys()),cols=1,
            specs=[[{"type": "scatter"}]] * len(search_term_ids.keys()),
            subplot_titles=[s["title"] for s in subplots],
            vertical_spacing=0.15,
        )
        
        # add subplot data to figure one at a time
        for i, subplot in enumerate(subplots):
            for trace in subplot["data"]:
                figure.add_trace(trace, row=(i+1), col=1)
                    
    else:
        figure.update_xaxes(range=[0,1])
        figure.update_yaxes(range=[0,1])
        figure.update_layout(
            title_text="No Data for Selected Criteria",
            yaxis_title="Count",
        )  
    figure.update_layout(height=height)
    
    return figure

# load options for VA trends time series
def load_ts_options(va_data, cod_groups=pd.DataFrame()):
    if cod_groups.empty:
        data_dir = "va_explorer/va_analytics/dash_apps/dashboard_data" 
        cod_groups = load_cod_groupings(data_dir=data_dir)

     # load cod groups
    all_options = [(cod_group, "group") for cod_group in cod_groups.columns[2:].tolist()]
        
    # load unique cods in selected data
    va_data = pd.DataFrame(va_data)
    if va_data.size > 0:
        unique_cods = va_data["cause"].unique().tolist()
        all_options += [(cod_name, "cod") for cod_name in unique_cods]
        
    # always load all-cause option
    all_options.append(("All Causes", "All causes.all"))

    return all_options
