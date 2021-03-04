from django.contrib.auth.mixins import PermissionRequiredMixin
from django.views.generic import TemplateView, View
from django.http import HttpResponse
from django.forms.models import model_to_dict
import pandas as pd

from va_explorer.va_data_management.models import Location, VerbalAutopsy
from va_explorer.utils.mixins import CustomAuthMixin


class DashboardView(CustomAuthMixin, PermissionRequiredMixin, TemplateView):
    template_name = "va_analytics/dashboard.html"
    permission_required = "va_analytics.view_dashboard"


dashboard_view = DashboardView.as_view()


# NOTE: At the moment, all roles who can view the Dashboard can also download
# the dashboard data
class DownloadCsv(CustomAuthMixin, PermissionRequiredMixin, View):
    permission_required = "va_analytics.view_dashboard"

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
            # get location and cod
            va_dict["location"] = va.location.name
            va_dict["cause"] = va.causes.all()[0].cause
            for ancestor in location_ancestors[va.location.id]:
                va_dict[ancestor.location_type] = ancestor.name
            va_data.append(va_dict)

        va_df = pd.DataFrame.from_records(va_data)
        # Create the HttpResponse object with the appropriate CSV header.
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="va_download.csv"'
        va_df.to_csv(response, index=False)

        return response


download_csv = DownloadCsv.as_view()
