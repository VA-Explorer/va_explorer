from django.contrib.auth.mixins import PermissionRequiredMixin
from django.views.generic import TemplateView, View
from django.http import HttpResponse
from django.forms.models import model_to_dict
import pandas as pd

from va_explorer.va_data_management.models import Location
from va_explorer.va_data_management.models import VerbalAutopsy
from va_explorer.va_data_management.models import PII_FIELDS
from va_explorer.va_data_management.models import REDACTED_STRING
from va_explorer.utils.mixins import CustomAuthMixin


class DashboardView(CustomAuthMixin, PermissionRequiredMixin, TemplateView):
    template_name = "va_analytics/dashboard.html"
    permission_required = "va_analytics.view_dashboard"


dashboard_view = DashboardView.as_view()


class DownloadCsv(CustomAuthMixin, PermissionRequiredMixin, View):
    permission_required = "va_analytics.download_data"

    def get(self, request, *args, **kwargs):
        valid_vas = self.request.user.verbal_autopsies() \
            .exclude(causes=None).prefetch_related("location").prefetch_related("causes")

        # Build a location ancestors lookup and add location information at all levels to all vas
        location_ancestors = { 
            location.id:location.get_ancestors() for location in Location.objects.filter(location_type="facility") 
        }

        va_data = []
        # extract COD and location-based fields for each va object and convert to dicts
        for va in valid_vas:
            # convert model object to dictionary
            va_dict = model_to_dict(va)
            # get location
            va_dict["location"] = ""
            if va.location:
                va_dict["location"] = va.location.name
                for ancestor in location_ancestors[va.location.id]:
                    va_dict[ancestor.location_type] = ancestor.name
            # get cause of death
            va_dict["cause"] = va.causes.all()[0].cause
            va_data.append(va_dict)

        va_df = pd.DataFrame.from_records(va_data)

        # If user cannot view PII, redact all PII fields:
        if not request.user.can_view_pii:
            for field in PII_FIELDS:
                va_df[field] = REDACTED_STRING

        # Create the HttpResponse object with the appropriate CSV header.
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="va_download.csv"'
        va_df.to_csv(response, index=False)

        return response


download_csv = DownloadCsv.as_view()
