from django import forms
from django.db.models import Q
from django.forms import DateField, ModelMultipleChoiceField, Select, SelectMultiple

from va_explorer.users.forms import LocationRestrictionsSelectMultiple
from va_explorer.va_data_management.models import CauseOfDeath, Location


# load COD options for export form
def get_cod_options():
    options = list(
        CauseOfDeath.objects.distinct("cause").values_list("cause", flat=True)
    )
    options.insert(0, "All")
    return [(o, o) for o in options]


class DateInput(forms.DateInput):
    input_type = "date"


class VADownloadForm(forms.Form):
    action = forms.ChoiceField(
        label="Action",
        choices=(("export", "Export Data"), ("download", "Download Data")),
        initial="download",
        widget=Select(),
        required=True,
        help_text="Either export data to an external database (i.e. DHIS2) or \
        download locally",
    )

    start_date = DateField(
        label="Earliest Date",
        required=False,
        widget=DateInput(attrs={"class": "datepicker"}),
        help_text="Earliest VA date to download",
    )

    end_date = DateField(
        label="Latest Date",
        required=False,
        widget=DateInput(attrs={"class": "datepicker"}),
        help_text="Latest VA date to download",
    )

    locations = ModelMultipleChoiceField(
        # Don't include 'Unknown' or Root/Country node in options
        queryset=Location.objects.all()
        .exclude(Q(location_type="country") | Q(name="Unknown"))
        .order_by("path"),
        widget=LocationRestrictionsSelectMultiple(
            attrs={"class": "location-restrictions-select"}
        ),
        required=False,
        help_text="Choose location(s) from which to download data",
    )

    causes = ModelMultipleChoiceField(
        queryset=CauseOfDeath.objects.distinct("cause").order_by("cause"),
        widget=SelectMultiple(attrs={"class": "cod-select"}),
        required=False,
        help_text="Filter data by Cause of Death (CoD)",
    )

    # which endpoint system you're exporting to. Only for exports (not downloads)
    export_config = forms.ChoiceField(
        disabled=True,
        label="<b>#TODO:</b> Export Endpoint",
        choices=(
            ("dhis2", "DHIS2"),
            ("postgres", "database2"),
            ("oracle", "database3..."),
        ),
        initial="dhis2",
        widget=Select(),
        required=False,
        help_text="Type of endpoint to export to",
    )

    format = forms.ChoiceField(
        label="Data Format",
        choices=(("csv", "csv"), ("json", "json")),
        initial="csv",
        widget=Select(),
        required=False,
    )

    # clean up params before sending request
    def clean(self, *args, **kwargs):
        """
        Normal cleanup
        """
        cleaned_data = super().clean(*args, **kwargs)

        # Convert location objects back to ids for API
        locs = cleaned_data.get("locations", [])
        if len(locs) > 0:
            cleaned_data["locations"] = ",".join([str(loc.pk) for loc in list(locs)])
        else:
            cleaned_data["locations"] = ""

        # make sure action is specified
        if "action" not in cleaned_data:
            cleaned_data["action"] = "download"

        # Convert any COD objects back to ids for API
        cods = cleaned_data.get("causes", [])
        if len(cods) > 0:
            cleaned_data["causes"] = ",".join([str(cod.cause) for cod in cods])
        else:
            cleaned_data["causes"] = None

        # convert format to lowercase
        cleaned_data["format"] = cleaned_data.get("format", "csv").lower()
        return cleaned_data
