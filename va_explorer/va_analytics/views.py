import logging

import pandas as pd
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.db.models import Count, F, Q
from django.views.generic import ListView, TemplateView
from numpy import round
from pandas import to_datetime as to_dt
from rest_framework.response import Response
from rest_framework.views import APIView
from .utils.loading import load_va_data

from va_explorer.users.models import User
from va_explorer.utils.mixins import CustomAuthMixin
from va_explorer.va_analytics.filters import SupervisionFilter
from va_explorer.va_data_management.utils.date_parsing import (
    get_submissiondates,
    parse_date,
)
from va_explorer.va_logs.logging_utils import write_va_log

LOGGER = logging.getLogger("event_logger")


class DashboardAPIView(APIView):
    def get(self, request, format=None):
        date_cutoff = None
        data = load_va_data(request.user, date_cutoff=date_cutoff)
        return Response(data)


class DashboardView(CustomAuthMixin, PermissionRequiredMixin, TemplateView):
    template_name = "va_analytics/dashboard.html"
    permission_required = "va_analytics.view_dashboard"


dashboard_view = DashboardView.as_view()


class UserSupervisionView(CustomAuthMixin, PermissionRequiredMixin, ListView):
    permission_required = "va_analytics.supervise_users"
    template_name = "va_analytics/user_supervision_view.html"
    model = User

    def get_queryset(self):
        # Restrict to VAs this user can access and prefetch related for performance
        queryset = (
            self.request.user.verbal_autopsies()
            .prefetch_related("location", "causes", "coding_issues")
            .exclude(Id10010="")
        )

        self.filterset = SupervisionFilter(
            data=self.request.GET or None, queryset=queryset
        )
        query_dict = self.request.GET.dict()
        query_keys = [k for k in query_dict if k != "csrfmiddlewaretoken"]
        if len(query_keys) > 0:
            query = ", ".join(
                [f"{k}: {query_dict[k]}" for k in query_keys if query_dict[k] != ""]
            )
            write_va_log(
                LOGGER, f"[supervision] Queried users for: {query}", self.request
            )

        return self.filterset.qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["filterset"] = self.filterset

        # group column(s) - figure out appropriate level of aggregation based on filter
        group_col = context["filterset"].form.data.get("group_col", "interviewer")
        if group_col == "interviewer":
            index_cols = ["interviewer", "facility"]
        elif group_col == "facility":
            index_cols = ["facility"]
        else:
            index_cols = [group_col]

        # sort by chosen field (default is count)
        sort_col = self.request.GET.get("order_by", "Total VAs")
        # if order_by param starts with -, sort in descending order. Otherwise, ascending
        is_ascending = sort_col.startswith("-")
        if is_ascending:
            sort_col = sort_col.lstrip("-")

        all_vas = (
            context["object_list"]
            .only("id", "submissiondate", "Id10011", "Id10010")
            .select_related("location")
            .select_related("causes")
            .select_related("coding_issues")
            .values(
                "id",
                "submissiondate",
                "Id10011",
                interviewer=F("Id10010"),
                facility=F("location__name"),
                cause=F("causes__cause"),
                errors=Count(
                    F("coding_issues"), filter=Q(coding_issues__severity="error")
                ),
                warnings=Count(
                    F("coding_issues"), filter=Q(coding_issues__severity="warning")
                ),
            )
        )
        va_df = pd.DataFrame(all_vas)

        if not va_df.empty:
            va_df["date"] = get_submissiondates(va_df)
            context["supervision_stats"] = (
                va_df.assign(date=lambda df: df["date"].apply(parse_date))
                .assign(date=lambda df: to_dt(df["date"], errors="coerce"))
                # only analyze vas with valid submission dates
                .query("date == date")
                .assign(
                    week_hash=lambda df: df["date"].dt.isocalendar().week
                                         + 52 * df["date"].dt.year
                )
                .groupby(group_col)
                .agg(
                    {
                        "id": "count",
                        "warnings": "sum",
                        "errors": "sum",
                        "week_hash": "nunique",
                        "date": "max",
                    }
                )
                .assign(submission_rate=lambda df: round(df["id"] / df["week_hash"], 2))
                .reset_index()
                .merge(va_df[index_cols].drop_duplicates())
                .assign(date=lambda df: df["date"].dt.date)
                .rename(
                    columns={
                        "id": "Total VAs",
                        "week_hash": "Weeks of Data",
                        "submission_rate": "VAs / week",
                        "date": "Last Submission",
                    }
                )
                .sort_values(by=sort_col, ascending=is_ascending)
            ).to_dict(orient="records")

        return context


user_supervision_view = UserSupervisionView.as_view()
