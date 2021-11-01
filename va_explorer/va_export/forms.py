from django import forms
from django.forms import ModelChoiceField, ModelMultipleChoiceField, RadioSelect, Select, SelectMultiple, DateField
from va_explorer.va_data_management.models import Location
from va_explorer.users.forms import LocationRestrictionsSelectMultiple

class DateInput(forms.DateInput):
    input_type = 'date'

class VADownloadForm(forms.Form):

    start_date = DateField(
        label="Earliest Date",
        required=False,
        widget=DateInput(attrs={'class': 'datepicker'}), 
        help_text="Earliest VA date to download"
    )

    end_date = DateField(
        label="Latest Date",
        required=False,
        widget=DateInput(attrs={'class': 'datepicker'}),
        help_text="Latest VA date to download"
    )

    locations = ModelMultipleChoiceField(
        queryset=Location.objects.all().order_by("path"),
        widget=LocationRestrictionsSelectMultiple(attrs={"class": "facility-restrictions-select"}),
        required=False,
        help_text="Choose a geography to download data from"
    )

    format = forms.ChoiceField(
        label="Data Format", 
        choices=(("csv", "csv"), ("json", "json")),
        initial="csv",
        widget=Select(),
        required=True,
    ) 

    # clean up params before sending request
    def clean(self, *args, **kwargs):
        """
        Normal cleanup
        """
        cleaned_data = super().clean(*args, **kwargs)
        # Convert location objects back to ids for API
        locs = cleaned_data.get('locations', [])
        if len(locs) > 0:
             cleaned_data['locations'] = ','.join([str(loc.pk) for loc in list(locs)])
        else:
            cleaned_data['locations'] = ''

#        convert format to lowercase
        cleaned_data['format'] = cleaned_data.get('format', 'csv').lower()

        return cleaned_data

    # def clean_location(self):
    #     loc_id = self.cleaned_data.get('location', None)
    #     if loc_id:
    #         location_name = Location.filter(pk=loc_id).first()
    #         if location_name:
    #             return location_name
    #         # raise error if no matching location for location id
    #         else:
    #             raise ValidationError(_('Invalid location ID'), code='invalid_loc_id')
    #     return None




