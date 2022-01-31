import json
import logging
from urllib.parse import urlencode

import pandas as pd
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib.auth.models import Group
from django.core import serializers
from django.db.models import Count, F, Q
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import ListView, TemplateView, View
from django.views.generic.edit import FormView
from numpy import round
from pandas import to_datetime as to_dt

from va_explorer.users.models import User
from va_explorer.utils.mixins import CustomAuthMixin
from va_explorer.va_analytics.filters import SupervisionFilter
from va_explorer.va_data_management.models import PII_FIELDS, REDACTED_STRING, Location
from va_explorer.va_data_management.utils.date_parsing import (
    get_submissiondates,
    parse_date,
)
from va_explorer.va_data_management.utils.location_assignment import fuzzy_match
from va_explorer.va_export.forms import VADownloadForm
from va_explorer.va_export.utils import get_loc_ids_for_filter
from va_explorer.va_logs.logging_utils import write_va_log

LOGGER = logging.getLogger("event_logger")


@method_decorator(csrf_exempt, name="dispatch")
class VaApi(CustomAuthMixin, View):
    permission_required = "va_analytics.download_data"

    def get(self, request, *args, **kwargs):
        # params = super(VaApi, self).get(self, request, *args, **kwargs)
        # get all query params
        params = request.GET
        # for nullity checks
        empty_values = (None, "None", "", [])

        # NOTE: using same filters as dashboard - exclude vas w/ null locations, unknown death dates, or unknown CODs
        matching_vas = (
            request.user.verbal_autopsies()
            .exclude(Id10023="dk")
            .exclude(location__isnull=True)
            .select_related("location")
            .annotate(
                date=F("Id10023"),
                cause=F("causes__cause"),
                loc_id=F("location__id"),
                loc_name=F("location__name"),
            )
        )

        # =========ID FILTER LOGIC=========================#
        # if list of VA IDs provided, only dowload VAs with matching IDs (bypassing all other logic).
        va_ids = params.get("ids", None)
        if va_ids not in empty_values:
            # if comma-separated string, split into list
            if type(va_ids) is str:
                if "," in va_ids:
                    va_ids = va_ids.split(",")
                # otherwise, just single ID string - wrap in list
                else:
                    va_ids = [va_ids]
            # merge in cause information before returning
            matching_vas = (
                matching_vas.filter(pk__in=va_ids)
                .select_related("causes")
                .annotate(cause=F("causes__cause"), cause_id=F("causes__pk"))
                .values()
            )
        # otherwise, proceed to check for other filters
        else:
            # =========LOCATION FILTER LOGIC===================#
            # if location query, filter down to VAs within chosen location's jurisdiction
            loc_query = params.get("locations", None)
            if loc_query:
                # get ids of all provided locations and their descendants
                match_list = get_loc_ids_for_filter(loc_query)

                # filter VA queryset down to just those with matching location_ids
                matching_vas = matching_vas.filter(location__id__in=match_list)

            # =========DATE FILTER LOGIC===================#
            # if start/end dates specified, filter to only VAs within time range
            start_date = params.get("start_date", None)
            end_date = params.get("end_date", None)

            if start_date not in empty_values:
                start_date = start_date[0] if type(start_date) is list else start_date
                matching_vas = matching_vas.filter(Id10023__gte=start_date)

            if end_date not in empty_values:
                end_date = end_date[0] if type(end_date) is list else end_date
                matching_vas = matching_vas.filter(Id10023__lte=end_date)

            # get causes for matching vas and convert to list of records
            matching_vas = (
                matching_vas.select_related("causes")
                .annotate(cause=F("causes__cause"), cause_id=F("causes__pk"))
                .values()
            )

            # =========COD FILTER LOGIC===================#
            cod_query = params.get("causes", None)
            if cod_query not in empty_values:
                # get all valid cod ids (TODO - make this work with if cod names provided)
                match_list = cod_query.split(",")
                # filter VA queryset down to just those with matching location_ids
                matching_vas = matching_vas.filter(cause__in=match_list)

        # =========DATA CLEANING (if any matching VAs)========#
        if matching_vas.count() > 0:
            # Build a location ancestors lookup and add location information at all levels to all vas
            location_ancestors = {
                location.id: location.get_ancestors()
                for location in Location.objects.filter(location_type="facility")
            }

            # extract COD and location-based fields for each va object and convert to dicts
            for va in matching_vas:
                for ancestor in location_ancestors[va["loc_id"]]:
                    va[ancestor.location_type] = ancestor.name

                # Clean up location fields.
                va["location"] = va["loc_name"]
                del (va["loc_name"], va["loc_id"])

            # convert results to dataframe
            va_df = pd.DataFrame.from_records(matching_vas)

            if "index" in va_df.columns:
                va_df.drop(columns=["index"], inplace=True)

            # If user cannot view PII, redact all PII fields:
            if not request.user.can_view_pii:
                for field in PII_FIELDS:
                    if field in va_df.columns:
                        va_df[field] = REDACTED_STRING

        # =========DATA FORMAT LOGIC===================#
        # convert VAs to proper format. Currently supports .csv (default) and .json
        fmt = params.get("format", "csv").lower().replace("/", "")
        # determine whether to download as attachment or return raw data (default: return raw)
        download = params.get("download", False)

        # download only for csv
        if fmt.endswith("csv"):
            # Create the HttpResponse object with the appropriate CSV header.
            response = HttpResponse(content_type="text/csv")
            # download raw csv (no metadata)
            response.write(va_df.to_csv(index=False))
            response["Content-Disposition"] = 'attachment; filename="va_download.csv"'
        # download for json
        elif fmt.endswith("json"):
            data = {"count": va_df.shape[0], "records": va_df.to_json(orient="records")}

            # Create HttpResponse object with appropriate JSON header
            response = HttpResponse(json.dumps(data), content_type="application/json")
            response["Content-Disposition"] = 'attachment; filename="va_download.json"'

        else:
            response = HttpResponse()
        write_va_log(LOGGER, f"downloaded data in {fmt} format", self.request)

        return response


va_api_view = VaApi.as_view()


class Index(CustomAuthMixin, PermissionRequiredMixin, TemplateView, FormView):
    permission_required = "va_analytics.download_data"
    form_class = VADownloadForm
    template_name = "va_export/index.html"
    success_url = "verbalautopsy"

    def form_valid(self, form):
        form_data = form.cleaned_data
        api_url = reverse("va_export:va_api") + "?" + urlencode(form_data)
        return redirect(api_url)


download_view = Index.as_view()
