from datetime import date, timedelta

import pandas as pd
from django.db.models import F
from pandas.tseries.offsets import DateOffset

from va_explorer.va_data_management.constants import REDACTED_STRING
from va_explorer.va_data_management.utils.date_parsing import (
    get_interview_dates,
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
    "Id10012",
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
    "Id10012",
    "Id10011",
    "Id10023",
]
VA_TABLE_ROWS = ["collected", "coded", "uncoded"]
VA_TABLE_COLUMNS = ["24", "1 week", "1 month", "Overall"]
VA_GRAPH_TYPES = VA_TABLE_ROWS

MONTHS = [START_MONTH + DateOffset(months=i) for i in range(12)]
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


def get_context_for_va_table(va_list, user):
    context = [
        {
            "id": va.id,
            "deceased": f"{va.Id10017} {va.Id10018}",
            "interviewer": va.Id10010,
            "interviewed": (
                parse_date(va.Id10012) if (va.Id10012 != "dk") else "Unknown"
            ),
            "dod": parse_date(va.Id10023) if (va.Id10023 != "dk") else "Unknown",
            "facility": va.location.name if va.location else "Not Provided",
            "cause": (
                va.causes.all()[0].cause if len(va.causes.all()) > 0 else "Not Coded"
            ),
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
    # Usually handled by filter, but not in this case
    for item in context:
        if not user.can_view_pii:
            item["deceased"] = REDACTED_STRING
    return context


# NOTE: using Id10012 (Interview date) to drive stats/views. submissiondate is
# unreliable or inaccurate due to bulk submissions
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
                "Id10012",
                name=F("Id10010"),
                facility=F("location__name"),
                cause=F("causes__cause"),
            )
        )

        va_df["date"] = get_interview_dates(va_df)

        # clean date fields - strip timezones from Id10012 (Interview date
        # created dates
        va_df["date"] = to_dt(va_df["date"])
        va_df["created"] = to_dt(va_df["created"])
        va_df["Id10023"] = to_dt(va_df["Id10023"])
        va_df["yearmonth"] = va_df["date"].dt.strftime("%Y-%m")

        # Load the VAs that are collected over various periods of time
        vas_24_hours = va_df[va_df["date"] == TODAY].index
        vas_1_week = va_df[va_df["date"] >= (TODAY - timedelta(days=7))].index
        vas_1_month = va_df[va_df["date"] >= (TODAY - DateOffset(months=1))].index
        vas_overall = va_df.sort_values(by="id").index

        # Graphs of the past 12 months, not including this month
        # (current month will almost always show month with artificially low numbers)
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

        # Use a local scope copy of VA_TABLE_FIELDS to avoid modifying the
        # original which would impact all future requests made by any user and
        # cause a ValueError: list.remove(x): x not in list
        user_va_table_fields = list(VA_TABLE_FIELDS)
        if user.is_fieldworker():
            user_va_table_fields.remove("Id10007")

        # List the VAs that need attention; requesting certain fields and
        # refetching makes this more efficient
        vas_to_address = (
            user_vas.only(*user_va_table_fields)
            .filter(causes__isnull=True)[:NUM_TABLE_ROWS]
            .prefetch_related("causes", "coding_issues", "location")
        )

        # List the VAs with Indeterminate COD
        vas_with_indeterminate_cod = (
            user_vas.only(*user_va_table_fields)
            .filter(causes__cause="Indeterminate")[:NUM_TABLE_ROWS]
            .prefetch_related("causes", "coding_issues", "location")
        )

        issue_list = get_context_for_va_table(vas_to_address, user)
        indeterminate_cod_list = get_context_for_va_table(
            vas_with_indeterminate_cod, user
        )

        # If there are more than NUM_TABLE_ROWS show a link to where
        # the rest can be seen
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
