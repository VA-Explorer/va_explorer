import json
import zipfile
from urllib.parse import urlencode

import pandas as pd
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.db.models import F
from django.http import HttpResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import TemplateView, View
from django.views.generic.edit import FormView

from va_explorer.utils.mixins import CustomAuthMixin
from va_explorer.va_data_management.constants import PII_FIELDS, REDACTED_STRING
from va_explorer.va_data_management.models import Location
from va_explorer.va_export.forms import VADownloadForm


@method_decorator(csrf_exempt, name="dispatch")
class VaApi(CustomAuthMixin, View):
    permission_required = "va_analytics.download_data"

    def post(self, request, *args, **kwargs):
        # params = super(VaApi, self).get(self, request, *args, **kwargs)
        # get all params
        params = request.POST

        # for nullity checks
        empty_values = (None, "None", "", [])

        # NOTE: using same filters as dashboard - exclude vas w/ null locations,
        # unknown death dates, or unknown CODs
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
        # if list of VA IDs provided, only download VAs with matching IDs
        # (bypassing all other logic).
        va_ids = params.get("ids", None)
        if va_ids not in empty_values:
            # if comma-separated string, split into list
            if isinstance(va_ids, str):
                # otherwise, just single ID string - wrap in list
                va_ids = va_ids.split(",") if "," in va_ids else [va_ids]
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
            # if location query, filter down VAs within chosen location's jurisdiction
            loc_query = params.get("locations", None)
            if loc_query:
                id_list = loc_query.split(",")

                # also add location descendants to id list
                locations_cache = Location.objects.filter(pk__in=id_list)
                for location in locations_cache:
                    id_list.extend(
                        location.get_descendants().values_list("id", flat=True)
                    )

                matching_vas = matching_vas.filter(location__id__in=id_list)

            # =========DATE FILTER LOGIC===================#
            # if start/end dates specified, filter to only VAs within time range
            start_date = params.get("start_date", None)
            end_date = params.get("end_date", None)

            if start_date not in empty_values:
                start_date = (
                    start_date[0] if isinstance(start_date, list) else start_date
                )
                matching_vas = matching_vas.filter(Id10023__gte=start_date)

            if end_date not in empty_values:
                end_date = end_date[0] if isinstance(end_date, list) else end_date
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
                # get all valid cod ids
                # #TODO - make this work with if cod names provided
                match_list = cod_query.split(",")
                # filter VA queryset down to just those with matching location_ids
                matching_vas = matching_vas.filter(cause__in=match_list)

        # =========DATA CLEANING (if any matching VAs)========#
        va_df = pd.DataFrame()

        if matching_vas.count() > 0:
            # Build a location ancestors lookup and add location information at
            # all levels to all vas
            location_ancestors = {
                location.id: location.get_ancestors()
                for location in Location.objects.filter(location_type="facility")
            }

            # extract COD and location-based fields for each va object and
            # convert to dicts
            for va in matching_vas:
                for ancestor in location_ancestors[va["loc_id"]]:
                    va[ancestor.location_type] = ancestor.name

                # Clean up location fields.
                va["location"] = va["loc_name"]
                del (va["loc_name"], va["loc_id"])

            # convert results to dataframe
            va_df = pd.DataFrame.from_records(matching_vas)

            if "index" in va_df.columns:
                va_df = va_df.drop(columns=["index"])

            # If user cannot view PII, redact all PII fields:
            if not request.user.can_view_pii:
                for field in PII_FIELDS:
                    if field in va_df.columns:
                        va_df[field] = REDACTED_STRING

        # =========DATA FORMAT LOGIC===================#
        # convert VAs to proper format. Currently supports .csv (default) and .json
        fmt = params.get("format", "csv").lower().replace("/", "")

        response = HttpResponse(content_type="application/zip")

        # download only for csv
        if fmt.endswith("csv"):
            response["Content-Disposition"] = "attachment; filename=export.csv.zip"
            response.status_code = 200

            # Write zip to response (must use zipfile.ZIP_DEFLATED for compression)
            z = zipfile.ZipFile(response, "w", zipfile.ZIP_DEFLATED)
            # Write csv file to zip
            z.writestr("va_download.csv", va_df.to_csv(index=False))
        # download for json
        elif fmt.endswith("json"):
            response["Content-Disposition"] = "attachment; filename=export.json.zip"
            response.status_code = 200

            # Write zip to response (must use zipfile.ZIP_DEFLATED for compression)
            z = zipfile.ZipFile(response, "w", zipfile.ZIP_DEFLATED)
            # Write JSON to zip
            z.writestr(
                "va_download.json",
                json.dumps(
                    {
                        "count": va_df.shape[0],
                        "records": va_df.to_json(orient="records"),
                    }
                ),
            )
        else:
            response = HttpResponse()
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
