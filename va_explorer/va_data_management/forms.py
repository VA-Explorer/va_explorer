from django import forms
from datetime import datetime
from .models import VerbalAutopsy
from .models import PII_FIELDS
from va_explorer.va_data_management.utils.date_parsing import parse_date
from config.settings.base import DATE_FORMATS



class VerbalAutopsyForm(forms.ModelForm):

    class Meta:
        model = VerbalAutopsy
        exclude = ('id', 'location', 'instanceid')

    def __init__(self, *args, **kwargs):
        include_pii = kwargs.pop('include_pii', True)
        super().__init__(*args, **kwargs)
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

        if "Id10023" in cleaned_data:
            validate_date_format(
                self, cleaned_data["Id10023"]
            )

        return cleaned_data

def validate_date_format(form, Id10023):
    """
    Custom form validation for field Id10023, date of death
    """
    # TODO add a date picker to the form so we don't have to check the string format
    if Id10023 != "dk":
        try: 
            parse_date(Id10023, strict=True)
        except ValueError:
            form._errors["Id10023"] = form.error_class(
                [f"Field Id10023 must be in \"dk\" if unknown or in one of following date formats: {list(DATE_FORMATS.values())}"]
            )
