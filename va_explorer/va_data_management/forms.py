from django import forms
from .models import VerbalAutopsy
from django.forms import ModelChoiceField, ModelMultipleChoiceField, RadioSelect, CharField, DateField
from bootstrap_datepicker_plus import DatePickerInput
from functools import partial

DateInput = partial(forms.DateInput, {'class': 'datepicker'})

class DateRangeForm(forms.Form):
    start_date = forms.DateField(widget=DateInput())
    end_date = forms.DateField(widget=DateInput())

class VerbalAutopsyForm(forms.ModelForm):

    class Meta:
        model = VerbalAutopsy
        exclude = ('id', 'location')

# class VAFilterForm(forms.ModelForm):

# 	# name = CharField(field_name="Id10007", lookup_expr="icontains", label="Name")
# 	# start_date = DateField(field_name="Id10023", lookup_expr="gte", label="Earliest Date", widget=DateInput())
# 	# end_date = DateField(field_name="Id10023", lookup_expr="lte", label="Latest Date", widget=DateInput())
# 	# location = CharField(field_name="location__name", lookup_expr="icontains", label="Facility")
# 	class Meta:
# 		model=VerbalAutopsy
# 		fields = ['Id10007', 'Id10023']
# 		widgets = {
# 	        #'Id10023': DatePickerInput(), # default date-format %m/%d/%Y will be used
# 	        'Id10023': DatePickerInput(format='%Y-%m-%d'), # specify date-frmat
# 	    }


class DatePickerForm(forms.Form):
    todo = forms.CharField(
        widget=forms.TextInput(attrs={"class": "form-control"})
    )
    date = forms.DateField(
        widget=DatePickerInput(format='%m/%d/%Y')
    )
