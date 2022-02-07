import datetime as dt
from urllib.parse import urlencode

import dash_bootstrap_components as dbc
import dash_html_components as html
from django.urls import reverse

from va_explorer.va_analytics.utils.plotting import load_lookup_dicts


def render_update_header(va_stats):
    header = html.Div(className="row", id="va_stats_header", children=[])
    if va_stats:
        assert "last_update" in va_stats and "last_submission" in va_stats
        if va_stats["last_update"] or va_stats["last_submission"]:
            if va_stats["last_update"]:
                update_desc = html.P(
                    children=[html.B("Last Data Update: "), va_stats["last_update"]],
                    style={"margin-left": "20px"},
                )
                header.children.append(update_desc)
            if va_stats["last_submission"]:
                submission_desc = html.P(
                    children=[
                        html.B("Last VA Submission: "),
                        html.Span(va_stats["last_submission"]),
                    ],
                    style={"margin-left": "10px"},
                )
                header.children.append(submission_desc)
            if va_stats.get("ineligible_vas", None):
                ineligible_tooltip = "VAs excluded from dashboard due to missing \
                                      location, date of death (Id10023) or both."
                ineligible_desc = html.P(
                    id="inelig-tooltip-target",
                    children=[
                        html.B("# of Ineligible VAs: "),
                        va_stats["ineligible_vas"],
                        html.Span(
                            className="fas fa-info-circle",
                            style={"margin-left": "3px", "color": "rgba(75,75,75,0.5)"},
                        ),
                        dbc.Tooltip(ineligible_tooltip, target="inelig-tooltip-target"),
                    ],
                    style={"margin-left": "10px"},
                )

                header.children.append(ineligible_desc)
    return header


# method to render download api url from dashboard params
def build_download_url(chosen_region=None, timeframe=None, cod=None, time_mapper=None):
    # logic to convert dashboard parameters into API query
    params = {}

    # location filter
    if chosen_region not in ["all", None]:
        params["locations"] = chosen_region

    # time filter
    if timeframe not in ["all", None]:
        if not time_mapper:
            time_mapper = load_lookup_dicts().get("time_dict")
        cutoff = dt.datetime.today() - dt.timedelta(days=time_mapper[timeframe])
        params["start_date"] = cutoff.strftime("%Y-%m-%d")

    # cod filter
    if cod not in ["all", None]:
        params["causes"] = cod

    # build URL
    api_url = reverse("va_export:va_api") + "?" + urlencode(params)
    return api_url
