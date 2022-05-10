from datetime import date, timedelta

import pandas as pd
from dateutil.relativedelta import relativedelta
from django.db.models import F
from django.http import JsonResponse
from django.views.generic import TemplateView, View

from va_explorer.utils.mixins import CustomAuthMixin
from va_explorer.va_data_management.utils.date_parsing import (
    get_submissiondates,
    parse_date,
    to_dt,
)
from va_explorer.va_data_management.utils.loading import get_va_summary_stats

TODAY = pd.to_datetime(date.today())
NUM_TABLE_ROWS = 5


class Index(CustomAuthMixin, TemplateView):
    template_name = "home/index.html"

    def get_context_data(self, **kwargs):
        # TODO: interviewers should only see their own data
        context = super().get_context_data(**kwargs)
        user = self.request.user

        context.update(get_va_summary_stats(user.verbal_autopsies()))

        context["locations"] = "All Regions"
        if user.location_restrictions.count() > 0:
            context["locations"] = ", ".join(
                [location.name for location in user.location_restrictions.all()]
            )

        return context


class Trends(CustomAuthMixin, View):
    def get(self, request, *args, **kwargs):
        (
            va_table,
            graphs,
            issue_list,
            indeterminate_cod_list,
            additional_issues,
            additional_indeterminate_cods,
        ) = self.get_page_data(request.user)

        return JsonResponse(
            {
                "vaTable": va_table,
                "graphs": graphs,
                "issueList": issue_list,
                "indeterminateCodList": indeterminate_cod_list,
                "additionalIssues": additional_issues,
                "additionalIndeterminateCods": additional_indeterminate_cods,
                "isFieldWorker": request.user.is_fieldworker(),
            }
        )

    def get_context_for_va_table(self, va_list):
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
                    [
                        issue
                        for issue in va.coding_issues.all()
                        if issue.severity == "error"
                    ]
                ),
            }
            for va in va_list
        ]

    def get_page_data(self, user):
        start_month = pd.to_datetime(date(TODAY.year - 1, TODAY.month, 1))

        # NOTE: using SUBMISSIONDATE to drive stats/views. To change this, change all references to submissiondate
        user_vas = user.verbal_autopsies()
        if user_vas.count() > 0:
            va_df = pd.DataFrame(
                user_vas.only(
                    "id",
                    "Id10023",
                    "location",
                    "Id10011",
                    "submissiondate",
                    "created",
                    "Id10010",
                    "Id10011",
                )
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
            vas_1_month = va_df[
                va_df["date"] >= (TODAY - relativedelta(months=1))
            ].index
            vas_overall = va_df.sort_values(by="id").index

            # Graphs of the past 12 months, not including this month (current month will almost
            # always show the month with artificially low numbers)
            plot_df = pd.DataFrame(
                {"month": [start_month + relativedelta(months=i) for i in range(12)]}
            ).assign(month_num=lambda df: df["month"].dt.month)

            months = [start_month + relativedelta(months=i) for i in range(12)]
            x = [month.strftime("%b") for month in months]
            plot_df = pd.DataFrame(
                {"yearmonth": [month.strftime("%Y-%m") for month in months], "x": x}
            )

            # Collected; total VAs by month
            plot_df = plot_df.merge(
                va_df.query("date >= @start_month")
                .groupby("yearmonth")["id"]
                .count()
                .rename("y_collected")
                .reset_index(),
                how="left",
            ).fillna(0)

            graphs = {
                "submittedChart": {
                    "x": plot_df["x"].values.tolist(),
                    "y": plot_df["y_collected"].values.tolist(),
                }
            }

            # Coded; same query as above, just filtered by whether the va has been coded
            plot_df = plot_df.merge(
                va_df.query("date >= @start_month & cause==cause")
                .groupby("yearmonth")["id"]
                .count()
                .rename("y_coded")
                .reset_index(),
                how="left",
            ).fillna(0)

            graphs["codedChart"] = {
                "x": plot_df["x"].values.tolist(),
                "y": plot_df["y_coded"].values.tolist(),
            }

            # Uncoded; just take the difference between the two previous queries
            graphs["notYetCodedChart"] = {
                "x": plot_df["x"].values.tolist(),
                "y": (plot_df["y_collected"] - plot_df["y_coded"]).values.tolist(),
            }

            # VAs successfully coded in the past 24 hours, 1 week, and 1 month
            vas_coded_24_hours = (
                va_df.loc[vas_24_hours, :].query("cause == cause").shape[0]
            )
            vas_coded_1_week = va_df.loc[vas_1_week, :].query("cause == cause").shape[0]
            vas_coded_1_month = (
                va_df.loc[vas_1_month, :].query("cause == cause").shape[0]
            )
            vas_coded_overall = (
                va_df.loc[vas_overall, :].query("cause == cause").shape[0]
            )

            va_table = {
                "collected": {
                    "24": len(vas_24_hours),
                    "1 week": len(vas_1_week),
                    "1 month": len(vas_1_month),
                    "Overall": len(vas_overall),
                },
                "coded": {
                    "24": vas_coded_24_hours,
                    "1 week": vas_coded_1_week,
                    "1 month": vas_coded_1_month,
                    "Overall": vas_coded_overall,
                },
                "uncoded": {
                    "24": len(vas_24_hours) - vas_coded_24_hours,
                    "1 week": len(vas_1_week) - vas_coded_1_week,
                    "1 month": len(vas_1_month) - vas_coded_1_month,
                    "Overall": len(vas_overall) - vas_coded_overall,
                },
            }

            # List the VAs that need attention; requesting certain fields and prefetching makes this more efficient
            vas_to_address = (
                user_vas.only(
                    "id",
                    "location_id",
                    "Id10007",
                    "Id10010",
                    "Id10017",
                    "Id10018",
                    "submissiondate",
                    "Id10011",
                    "Id10023",
                )
                .filter(causes__isnull=True)[:NUM_TABLE_ROWS]
                .prefetch_related("causes", "coding_issues", "location")
            )

            # List the VAs with Indeterminate COD
            vas_with_indeterminate_cod = (
                user_vas.only(
                    "id",
                    "location_id",
                    "Id10007",
                    "Id10010",
                    "Id10017",
                    "Id10018",
                    "submissiondate",
                    "Id10011",
                    "Id10023",
                )
                .filter(causes__cause="Indeterminate")[:NUM_TABLE_ROWS]
                .prefetch_related("causes", "coding_issues", "location")
            )

            issue_list = self.get_context_for_va_table(vas_to_address)
            indeterminate_cod_list = self.get_context_for_va_table(
                vas_with_indeterminate_cod
            )

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


trends_endpoint_view = Trends.as_view()


class About(CustomAuthMixin, TemplateView):
    template_name = "home/about.html"
