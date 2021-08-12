from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib.auth.models import Group
from django.views.generic import TemplateView, View, ListView
from django.http import HttpResponse
from django.db.models import F
import logging
import pandas as pd


from va_explorer.va_data_management.models import Location
from va_explorer.va_data_management.models import PII_FIELDS
from va_explorer.va_data_management.models import REDACTED_STRING
from va_explorer.va_data_management.utils.validate import parse_date
from va_explorer.users.models import User
from va_explorer.va_logs.logging_utils import write_va_log

from va_explorer.va_analytics.filters import SupervisionFilter
from va_explorer.utils.mixins import CustomAuthMixin

LOGGER = logging.getLogger("event_logger")

class DashboardView(CustomAuthMixin, PermissionRequiredMixin, TemplateView):
    template_name = "va_analytics/dashboard.html"
    permission_required = "va_analytics.view_dashboard"


dashboard_view = DashboardView.as_view()

class DownloadCsv(CustomAuthMixin, PermissionRequiredMixin, View):
    permission_required = "va_analytics.download_data"

    def get(self, request, date_cutoff="1901-01-01", *args, **kwargs,):
        # NOTE: using same filters as dashboard - exclude vas w/ null locations, unknown death dates, or unknown CODs 
        valid_vas = self.request.user \
        .verbal_autopsies(date_cutoff=date_cutoff) \
        .exclude(Id10023="dk") \
        .exclude(location__isnull=True) \
        .select_related("location") \
        .select_related("causes") \
        .annotate(date=F("Id10023"),\
                 cause=F("causes__cause"), \
                 loc_id=F('location__id'), \
                 loc_name=F('location__name')) \
        .values()
    
        # Build a location ancestors lookup and add location information at all levels to all vas
        location_ancestors = { 
            location.id:location.get_ancestors() for location in Location.objects.filter(location_type="facility") 
        }

        # extract COD and location-based fields for each va object and convert to dicts
        for va in valid_vas:
            
            for ancestor in location_ancestors[va['loc_id']]:
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
    paginate_by = 15

    def get_queryset(self):
        # Restrict to VAs this user can access and prefetch related for performance
        queryset = self.request.user.verbal_autopsies().prefetch_related("location", "causes", "coding_issues").exclude(username='')

        self.filterset = SupervisionFilter(data=self.request.GET or None, queryset=queryset)
        query_dict = self.request.GET.dict()
        query_keys = [k for k in query_dict if k != 'csrfmiddlewaretoken']
        if len(query_keys) > 0:
            query = ', '.join([f"{k}: {query_dict[k]}" for k in query_keys if query_dict[k] != ""])
            write_va_log(LOGGER, f"[supervision] Queried users for: {query}", self.request)

        return self.filterset.qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["filterset"] = self.filterset
        #parse_date(va.Id10023)
        va_data = [{
            "id": va.id,
            "interviewer": va.username,
            "date":  parse_date(va.submissiondate, strict=False),
            "facility": va.location.name if va.location else "",
            "cause": va.causes.first().cause if va.causes.count() > 0 else "",
            "warnings": va.coding_issues.filter(severity='warning').count(),
            "errors": va.coding_issues.filter(severity='error').count()
        } for va in context['object_list']]
        va_df = pd.DataFrame(va_data)
        context['worker_stats'] = (va_df
            .assign(date = lambda df: pd.to_datetime(df['date'], utc=True))
            .assign(week_hash=lambda df: df['date'].dt.isocalendar().week + 52 * df['date'].dt.year)
            .groupby('interviewer')
            .agg({'id': 'count', 'warnings': 'sum', 'errors': 'sum', 'week_hash': 'nunique'})
            .rename(columns={'id': 'total_vas', 'week_hash': 'weeks_worked'})
            .assign(submission_rate = lambda df: df['total_vas'] / df['weeks_worked'])
            .reset_index()
            .merge(va_df[['interviewer', 'facility']].drop_duplicates())
        ).to_dict(orient='records')
        #context.update(get_va_summary_stats(self.filterset.qs))
        return context



user_supervision_view = UserSupervisionView.as_view()
