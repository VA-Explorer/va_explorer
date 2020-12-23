from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView
from django.http import HttpResponse
import pandas as pd
from django.forms.models import model_to_dict
from va_explorer.va_data_management.models import Location, VerbalAutopsy


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "va_analytics/dashboard.html"


dashboard_view = DashboardView.as_view()


@login_required
def download_csv(request, out_file="va_download.csv"):

    # pull in va records with CODs from database 
    valid_vas = VerbalAutopsy.objects.exclude(causes=None).prefetch_related("location").prefetch_related("causes")

    # Build a location ancestors lookup and add location information at all levels to all vas
    location_ancestors = { location.id:location.get_ancestors() for location in Location.objects.filter(location_type="facility") }
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
    response["Content-Disposition"] = f'attachment; filename="{out_file}"'
    
    va_df.to_csv(response, index=False)
    
    return response
    
