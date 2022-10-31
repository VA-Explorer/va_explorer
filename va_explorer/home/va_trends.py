from datetime import date, timedelta

import pandas as pd
from django.db.models import F
from pandas._libs.tslibs.offsets import relativedelta

from va_explorer.va_data_management.utils.date_parsing import (
    get_submissiondates,
    parse_date,
    to_dt,
)

TODAY = pd.to_datetime(date.today())
START_MONTH = pd.to_datetime(date(TODAY.year - 1, TODAY.month, 1))

NUM_TABLE_ROWS = 5
VA_DF_FIELDS = [
    "id",
    "Id10023",
    "location",
    "Id10011",
    "submissiondate",
    "created",
    "Id10010",
    "Id10011",
]
VA_TABLE_FIELDS = [
    "id",
    "location_id",
    "Id10007",
    "Id10010",
    "Id10017",
    "Id10018",
    "submissiondate",
    "Id10011",
    "Id10023",
]
VA_TABLE_ROWS = ["collected", "coded", "uncoded"]
VA_TABLE_COLUMNS = ["24", "1 week", "1 month", "Overall"]
VA_GRAPH_TYPES = VA_TABLE_ROWS

MONTHS = [START_MONTH + relativedelta(months=i) for i in range(12)]
VA_GRAPH_Y_DATA = 12 * [0.0]
VA_GRAPH_X_DATA = [month.strftime("%Y-%m") for month in MONTHS]


def empty_va_table():
    table = {}
    table_data = {}

    for col in VA_TABLE_COLUMNS:
        table_data[col] = 0
    for row in VA_TABLE_ROWS:
        table[row] = table_data.copy()

    return table


def empty_graph_data():
    graphs = {}

    for graph_type in VA_GRAPH_TYPES:
        graphs[graph_type] = {}
        graphs[graph_type] = {}

    for graph_type in VA_GRAPH_TYPES:
        graphs[graph_type]["x"] = VA_GRAPH_X_DATA.copy()
        graphs[graph_type]["y"] = VA_GRAPH_Y_DATA.copy()

    return graphs


def get_context_for_va_table(va_list):
    return [
        {
            "id": va.id,
            "deceased": f"{va.Id10017} {va.Id10018}",
            "interviewer": va.Id10010,
            "submitted": parse_date(va.submissiondate)
            if (va.submissiondate != "dk")
            else "Unknown",  # django stores the date in yyyy-mm-dd
            "dod": parse_date(va.Id10023) if (va.Id10023 != "dk") else "Unknown",
            "facility": va.location.name if va.location else "",
            "cause": va.causes.all()[0].cause if len(va.causes.all()) > 0 else "",
            "warnings": len(
                [
                    issue
                    for issue in va.coding_issues.all()
                    if issue.severity == "warning"
                ]
            ),
            "errors": len(
                [issue for issue in va.coding_issues.all() if issue.severity == "error"]
            ),
        }
        for va in va_list
    ]


# NOTE: using SUBMISSIONDATE to drive stats/views. To change this, change all references to submissiondate
def get_trends_data(user):
    user_vas = user.verbal_autopsies()
    va_table = empty_va_table()
    graphs = empty_graph_data()
    issue_list = []
    indeterminate_cod_list = []
    additional_issues = 0
    additional_indeterminate_cods = 0

    if user_vas.count() > 0:
        va_df = pd.DataFrame(
            user_vas.only(*VA_DF_FIELDS)
            .select_related("location")
            .select_related("causes")
            .values(
                "id",
                "Id10023",
                "created",
                "Id10011",
                "submissiondate",
                name=F("Id10010"),
                facility=F("location__name"),
                cause=F("causes__cause"),
            )
        )

        va_df["date"] = get_submissiondates(va_df)

        # clean date fields - strip timezones from submissiondate and created dates
        va_df["date"] = to_dt(va_df["date"])
        va_df["created"] = to_dt(va_df["created"])
        va_df["Id10023"] = to_dt(va_df["Id10023"])
        va_df["yearmonth"] = va_df["date"].dt.strftime("%Y-%m")

        # Load the VAs that are collected over various periods of time
        vas_24_hours = va_df[va_df["date"] == TODAY].index
        vas_1_week = va_df[va_df["date"] >= (TODAY - timedelta(days=7))].index
        vas_1_month = va_df[va_df["date"] >= (TODAY - relativedelta(months=1))].index
        vas_overall = va_df.sort_values(by="id").index

        # Graphs of the past 12 months, not including this month (current month will almost
        # always show the month with artificially low numbers)
        x = [month.strftime("%b") for month in MONTHS]
        plot_df = pd.DataFrame({"yearmonth": VA_GRAPH_X_DATA, "x": x})

        # Collected; total VAs by month
        plot_df = plot_df.merge(
            va_df.query("date >= @START_MONTH")
            .groupby("yearmonth")["id"]
            .count()
            .rename("y_collected")
            .reset_index(),
            how="left",
        ).fillna(0)

        graphs["collected"]["x"] = plot_df["x"].values.tolist()
        graphs["collected"]["y"] = plot_df["y_collected"].values.tolist()

        # Coded; same query as above, just filtered by whether the va has been coded
        plot_df = plot_df.merge(
            va_df.query("date >= @START_MONTH & cause==cause")
            .groupby("yearmonth")["id"]
            .count()
            .rename("y_coded")
            .reset_index(),
            how="left",
        ).fillna(0)

        graphs["coded"]["x"] = plot_df["x"].values.tolist()
        graphs["coded"]["y"] = plot_df["y_coded"].values.tolist()

        # Uncoded; just take the difference between the two previous queries
        graphs["uncoded"]["x"] = plot_df["x"].values.tolist()
        graphs["uncoded"]["y"] = (
            plot_df["y_collected"] - plot_df["y_coded"]
        ).values.tolist()

        # VAs successfully coded in the past 24 hours, 1 week, and 1 month
        vas_coded_24_hours = va_df.loc[vas_24_hours, :].query("cause == cause").shape[0]
        vas_coded_1_week = va_df.loc[vas_1_week, :].query("cause == cause").shape[0]
        vas_coded_1_month = va_df.loc[vas_1_month, :].query("cause == cause").shape[0]
        vas_coded_overall = va_df.loc[vas_overall, :].query("cause == cause").shape[0]

        va_table["collected"]["24"] = len(vas_24_hours)
        va_table["collected"]["1 week"] = len(vas_1_week)
        va_table["collected"]["1 month"] = len(vas_1_month)
        va_table["collected"]["Overall"] = len(vas_overall)
        va_table["coded"]["24"] = vas_coded_24_hours
        va_table["coded"]["1 week"] = vas_coded_1_week
        va_table["coded"]["1 month"] = vas_coded_1_month
        va_table["coded"]["Overall"] = vas_coded_overall
        va_table["uncoded"]["24"] = len(vas_24_hours) - vas_coded_24_hours
        va_table["uncoded"]["1 week"] = len(vas_1_week) - vas_coded_1_week
        va_table["uncoded"]["1 month"] = len(vas_1_month) - vas_coded_1_month
        va_table["uncoded"]["Overall"] = len(vas_overall) - vas_coded_overall

        if user.is_fieldworker():
            VA_TABLE_FIELDS.remove("Id10007")

        # List the VAs that need attention; requesting certain fields and prefetching makes this more efficient
        vas_to_address = (
            user_vas.only(*VA_TABLE_FIELDS)
            .filter(causes__isnull=True)[:NUM_TABLE_ROWS]
            .prefetch_related("causes", "coding_issues", "location")
        )

        # List the VAs with Indeterminate COD
        vas_with_indeterminate_cod = (
            user_vas.only(*VA_TABLE_FIELDS)
            .filter(causes__cause="Indeterminate")[:NUM_TABLE_ROWS]
            .prefetch_related("causes", "coding_issues", "location")
        )

        issue_list = get_context_for_va_table(vas_to_address)
        indeterminate_cod_list = get_context_for_va_table(vas_with_indeterminate_cod)

        # If there are more than NUM_TABLE_ROWS show a link to where the rest can be seen
        additional_issues = max(
            (len(vas_overall) - vas_coded_overall) - NUM_TABLE_ROWS, 0
        )
        additional_indeterminate_cods = max(
            user_vas.only("id").filter(causes__cause="Indeterminate").count()
            - NUM_TABLE_ROWS,
            0,
        )

    return (
        va_table,
        graphs,
        issue_list,
        indeterminate_cod_list,
        additional_issues,
        additional_indeterminate_cods,
    )
