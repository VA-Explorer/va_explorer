from django import forms
from datetime import datetime
from .models import VerbalAutopsy

class VerbalAutopsyForm(forms.ModelForm):

    class Meta:
        model = VerbalAutopsy
        exclude = ('id', 'location')
    
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
            datetime.strptime(Id10023, "%Y-%m-%d")
        except ValueError:
            form._errors["Id10023"] = form.error_class(
                ["Field Id10023 must be in the format yyyy-mm-dd or \"dk\" if unknown"]
            )
