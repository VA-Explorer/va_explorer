from django import forms

from config.settings.base import DATE_FORMATS
from va_explorer.va_data_management.utils.date_parsing import parse_date

from .constants import PII_FIELDS, FORM_FIELDS, HIDDEN_FIELDS, _date_fields
from .models import VerbalAutopsy


class VerbalAutopsyForm(forms.ModelForm):
    class Meta:
        model = VerbalAutopsy
        exclude = HIDDEN_FIELDS
        widgets = {}
        # Because (the massive amount of) model fields are textarea by default,
        # we are overriding the display logic via here + mappings in .constants
        for form_field in FORM_FIELDS["text"]:
            widgets[form_field] = forms.TextInput()
        for form_field in FORM_FIELDS["radio"]:
            widgets[form_field] = forms.RadioSelect(
                choices=FORM_FIELDS["radio"][form_field], attrs={"class": "va-check"}
            )
        for form_field in FORM_FIELDS["checkbox"]:
            widgets[form_field] = forms.CheckboxSelectMultiple(
                choices=FORM_FIELDS["checkbox"][form_field], attrs={"class": "va-check"}
            )
        for form_field in FORM_FIELDS["dropdown"]:
            widgets[form_field] = forms.Select(choices=FORM_FIELDS["dropdown"][form_field])
        for form_field in FORM_FIELDS["number"]:
            widgets[form_field] = forms.NumberInput()
        for form_field in FORM_FIELDS["date"]:
            widgets[form_field] = forms.DateInput()
        for form_field in FORM_FIELDS["time"]:
            widgets[form_field] = forms.TimeInput()
        for form_field in FORM_FIELDS["datetime"]:
            widgets[form_field] = forms.DateTimeInput()
        for form_field in FORM_FIELDS["display"]:
            widgets[form_field] = forms.TextInput(attrs={'readonly': 'readonly'})


    def __init__(self, *args, **kwargs):
        include_pii = kwargs.pop("include_pii", True)
        super().__init__(*args, **kwargs)
        # Handle text/textarea input types
        for _, field in self.fields.items():
            if not field.widget.attrs.get("class"):
                field.widget.attrs["class"] = "form-control"
            if isinstance(field.widget, forms.Textarea):
                field.widget.attrs["rows"] = "3"

        if not include_pii:
            for field in PII_FIELDS:
                del self.fields[field]

    # TODO: to display the error msgs properly, we need to use crispy forms in the template
    # for now we will just display the errors at the top of the page
    def clean(self, *args, **kwargs):
        """
        Normal cleanup
        """
        cleaned_data = super(VerbalAutopsyForm, self).clean(*args, **kwargs)

        # Validate that each date field has a valid date in the cleaned_data
        # Excludes calculated date fields because they are no longer editable
        for field in _date_fields:
            if cleaned_data[field]:
                self.validate_date_format(cleaned_data[field], field)

        return cleaned_data

    def validate_date_format(form, field_value, field):
        # TODO add a date picker to each date field to improve the user experience
        # TODO find a way to collect all of the date validation errors and show the message once
        if field_value != "dk":
            try:
                parse_date(field_value, strict=True)
            except ValueError:
                error_description = f'{field} must be "DK" if unknown or in one of \
                          following date formats: {list(DATE_FORMATS.values())}'
                form.add_error(field, error_description)
