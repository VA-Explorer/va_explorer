#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Feb 10 23:56:26 2021

@author: babraham
"""
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objs as go
from plotly.subplots import make_subplots

# ===========PLOTTING PROPERTIES/VARIABLES=====================#
D3 = px.colors.qualitative.D3
PLOTLY = px.colors.qualitative.Plotly


# plotting properties defined below
# ======= LOTTING PROPERTIES ==============#
def load_lookup_dicts():
    lookup = dict()
    # dictionary mapping time labels to days (or all)
    lookup["time_dict"] = {"today": 1, 
                          "last week": 7,
                          "last month": 30,
                          "last 6 months": 30.4 * 6, # last 182.5 days
                          "last year": 365,
                          "all": "all"}
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
    # dictionary mapping raw map metrics to human-readable names
    lookup["metric_names"] = {
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
        lookup = LOOKUP["death_location_names"]
        loc_cts["location"] = loc_cts["location"].apply(
            lambda x: lookup.get(x.lower(), x.capitalize())
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
        gender_labels = ['']
        gender_counts = [0]
        comb_fig.add_trace(
            go.Bar(
                name="Gender",
                x=gender_labels,
                y=gender_counts,
                text=gender_labels,
                textposition="auto",
                showlegend=False,
                marker_color=PLOTLY,
            ),
        )

        age_labels = ['']
        age_counts = [0]
        comb_fig.add_trace(
            go.Bar(
                name="Age Group",
                x=age_labels,
                y=age_counts,
                text=age_labels,
                textposition="auto",
                showlegend=False,
                marker_color=D3,
            ),
            row=1,
            col=2,
        )
        place_labels = ['']
        place_counts = [0]
        comb_fig.add_trace(
            go.Bar(
                name="Place of Death",  
                x=place_counts,
                y=place_labels,
                text=place_labels,
                textposition="auto",
                orientation="h",
                showlegend=False,
                marker_color=D3[4],
            ),
            row=2,
            col=1,
        )
        comb_fig.update_xaxes(range=[0,1])
        comb_fig.update_yaxes(range=[0,1])
        title = "No Data for Selected Criteria"

    if no_grids:
        comb_fig.update_xaxes(showgrid=False)
        comb_fig.update_yaxes(showgrid=False)

    if title:
        comb_fig.update_layout(title_text=title)

    return comb_fig.update_layout(height=height)


# ===========CAUSE OF DEATH PLOT LOGIC=========================#
# plot top N causes of death in va_data either overall or by factor/demographic
def cause_of_death_plot(va_df, factor, N=10, chosen_cod="all"):
    figure = go.Figure()
    factor = factor.lower()
    plot_fn = go.Bar

    if factor != "all":
        assert factor in ["age group", "sex", "place of death"]
        factor_col = LOOKUP["demo_to_col"][factor]
        factor_title = "by " + factor.capitalize()
        counts = va_df.pivot_table(
            index="cause",
            columns=factor_col,
            values="id",
            aggfunc=pd.Series.nunique,
            fill_value=0,
            margins=True,
        )
    else:
        counts = pd.DataFrame({"All": va_df.cause.value_counts()})
        factor_title = "Overall"

    if va_df.size > 0:
        # make index labels pretty
        counts.index = [LOOKUP["metric_names"].get(x, x) for x in counts.index]
        counts["cod"] = counts.index
        counts = (
            counts[counts["cod"] != "All"].sort_values(by="All", ascending=False).head(N)
        )
        groups = list(set(counts.columns).difference(set(["cod"])))

        lines = [LOOKUP["line_colors"]["secondary"] for j in range(len(counts["cod"]))]
        widths = np.repeat(1, len(counts["cod"]))
        if chosen_cod != "all":
            chosen_cod = LOOKUP["metric_names"].get(chosen_cod, chosen_cod.capitalize())
            if chosen_cod in counts.index:
                chosen_idx = counts.index.get_loc(chosen_cod)
                lines[chosen_idx] = "#e0b816"
                widths[chosen_idx] = 4
                counts["cod"][chosen_idx] = "<b>" + counts["cod"][chosen_idx] + "</b>"

        if factor != "all":
            groups.remove("All")
        for i, group in enumerate(groups):
            if factor == "all":
                # calculate percent as % of all cods (column-wise calculation)
                counts[f"{group}_pct"] = np.round(
                    100 * counts[group] / counts[group].sum(), 1
                )
            else:
                # calculate percent as % across groups for specific cod (row-wise calculation)
                counts[f"{group}_pct"] = counts.apply(
                    lambda row: np.round(100 * row[group] / row[groups].sum(), 1), axis=1
                )
            counts["text"] = (
                f"<i>{group.capitalize()}</i>: "
                + counts[group].astype(str)
                + " ("
                + counts[f"{group}_pct"].astype(str)
                + " %)"
            )

            # counts
            figure.add_trace(
                plot_fn(
                    y=counts[group],
                    x=counts["cod"],
                    text=counts["text"],
                    name=group.capitalize(),
                    orientation="v",
                    hovertemplate="<b>%{x}</b><br>%{text}<extra></extra>",
                    marker=dict(
                        color=LOOKUP["color_list"][i], line=dict(color=lines, width=widths),
                    ),
                )
            )
            # percents
            figure.add_trace(
                plot_fn(
                    y=counts[f"{group}_pct"],
                    x=counts["cod"],
                    text=counts["text"],
                    hovertemplate="<b>%{x}</b> <br> %{text}<extra></extra>",
                    name=group.capitalize(),
                    orientation="v",
                    visible=False,
                    marker=dict(
                        color=LOOKUP["color_list"][i], line=dict(color=lines, width=widths),
                    ),
                )
            )
            figure.update_layout(
                barmode="stack",
                title_text="Top Causes of Death {}".format(factor_title),
                xaxis_tickangle=-45,
                yaxis_title="Count",
                updatemenus=[
                    dict(
                        type="buttons",
                        direction="right",
                        x=1,
                        y=1.2,
                        active=0,
                        buttons=list(
                            [
                                dict(
                                    label="Counts",
                                    method="update",
                                    args=[
                                        {"visible": [True, False] * len(groups)},
                                        {"yaxis": {"title": "Count"}},
                                    ],
                                ),
                                dict(
                                    label="Percents",
                                    method="update",
                                    args=[
                                        {"visible": [False, True] * len(groups)},
                                        {"yaxis": {"title": "% of Total"}},
                                    ],
                                ),
                            ]
                        ),
                    )
                ],
            )   
    else:
        cod_labels = ['']
        cod_counts = [0]
        # counts
        figure.add_trace(
            plot_fn(
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


# ========TREND/TIMESERIES PLOT LOGI======================#
def va_trend_plot(va_df, group_period, factor="All", title=None):
    figure = go.Figure()
    group_period = group_period.lower()
    aggregate_title = group_period.capitalize()

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

        dtype = "category" if group_period == "year" else "date"

        factor = factor.lower()
        if factor != "all":
            assert factor in LOOKUP["demo_to_col"]
            factor_col = LOOKUP["demo_to_col"][factor]
            trend_counts = va_df.pivot_table(
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
                va_df[["timegroup", "id"]]
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
        if not title:
            title = "VA Counts by {}".format(aggregate_title)
        figure.update_layout(
            title_text=title,
            xaxis_title=aggregate_title,
            yaxis_title="Count",
            xaxis_type=dtype,
            xaxis_tickangle=-45,
            xaxis_tickformatstops=[
                dict(
                    dtickrange=[None, None],
                    value=LOOKUP["date_display_formats"].get(group_period, "%d/%m/%Y"),
                )
            ],
        )
    else:
        trend_labels = ['']
        trend_counts = [0]
        # counts
        figure.add_trace(
            go.Bar(
                y=trend_counts,
                x=trend_labels,
                name="no data",
                orientation="v",
            )
        )
        figure.update_xaxes(range=[0,1])
        figure.update_yaxes(range=[0,1])
        figure.update_layout(
            title_text="No Data for Selected Criteria",
            yaxis_title="Count",
        )  

    return figure
