import logging

import pandas as pd
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib.auth.models import Group
from django.db.models import Count, F, Q
from django.http import HttpResponse
from django.views.generic import ListView, TemplateView, View
from numpy import round

from va_explorer.users.models import User
from va_explorer.utils.mixins import CustomAuthMixin
from va_explorer.va_analytics.filters import SupervisionFilter
from va_explorer.va_data_management.models import PII_FIELDS, REDACTED_STRING, Location
from va_explorer.va_data_management.utils.validate import parse_date
from va_explorer.va_logs.logging_utils import write_va_log

LOGGER = logging.getLogger("event_logger")


class DashboardView(CustomAuthMixin, PermissionRequiredMixin, TemplateView):
    template_name = "va_analytics/dashboard.html"
    permission_required = "va_analytics.view_dashboard"


dashboard_view = DashboardView.as_view()


class DownloadCsv(CustomAuthMixin, PermissionRequiredMixin, View):
    permission_required = "va_analytics.download_data"

    def get(
        self, request, date_cutoff="1901-01-01", *args, **kwargs,
    ):
        # NOTE: using same filters as dashboard - exclude vas w/ null locations, unknown death dates, or unknown CODs
        valid_vas = (
            self.request.user.verbal_autopsies(date_cutoff=date_cutoff)
            .exclude(Id10023="dk")
            .exclude(location__isnull=True)
            .select_related("location")
            .select_related("causes")
            .annotate(
                date=F("Id10023"),
                cause=F("causes__cause"),
                loc_id=F("location__id"),
                loc_name=F("location__name"),
            )
            .values()
        )

        # Build a location ancestors lookup and add location information at all levels to all vas
        location_ancestors = {
            location.id: location.get_ancestors()
            for location in Location.objects.filter(location_type="facility")
        }

        # extract COD and location-based fields for each va object and convert to dicts
        for va in valid_vas:

            for ancestor in location_ancestors[va["loc_id"]]:
                va[ancestor.location_type] = ancestor.name

            # Clean up location fields.
            va["location"] = va["loc_name"]
            del (va["loc_name"], va["loc_id"])

        va_df = pd.DataFrame.from_records(valid_vas)

        if "index" in va_df.columns:
            va_df.drop(columns=["index"], inplace=True)

        # If user cannot view PII, redact all PII fields:
        if not request.user.can_view_pii:
            for field in PII_FIELDS:
                if field in va_df.columns:
                    va_df[field] = REDACTED_STRING

        # Create the HttpResponse object with the appropriate CSV header.
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="va_download.csv"'
        va_df.to_csv(response, index=False)

        write_va_log(LOGGER, f"[download] clicked download data", self.request)

        return response


download_csv = DownloadCsv.as_view()


class UserSupervisionView(CustomAuthMixin, PermissionRequiredMixin, ListView):
    permission_required = "va_analytics.supervise_users"
    template_name = "va_analytics/user_supervision_view.html"
    model = User

    def get_queryset(self):
        # Restrict to VAs this user can access and prefetch related for performance
        queryset = (
            self.request.user.verbal_autopsies()
            .prefetch_related("location", "causes", "coding_issues")
            .exclude(username="")
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
            .only("id", "submissiondate", "username")
            .select_related("location")
            .select_related("causes")
            .select_related("coding_issues")
            .values(
                "id",
                interviewer=F("username"),
                date=F("submissiondate"),
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
            context["supervision_stats"] = (
                va_df.assign(date=lambda df: pd.to_datetime(df["date"], utc=True))
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
