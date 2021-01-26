import django_filters
from django import forms

from .models import *
from django_filters import DateFilter, CharFilter, DateRangeFilter

from functools import partial

#DateInput = partial(forms.DateInput, {'class': 'datepicker'})
class DateInput(forms.DateInput):
    input_type = 'date'

class VAFilter(django_filters.FilterSet):
	name = CharFilter(field_name="Id10007", lookup_expr="icontains", label="Name")
	start_date = DateFilter(field_name="Id10023", lookup_expr="gte", label="Earliest Date", widget=DateInput(attrs={'class': 'datepicker'}))
	end_date = DateFilter(field_name="Id10023", lookup_expr="lte", label="Latest Date", widget=DateInput(attrs={'class': 'datepicker'}))
	location = CharFilter(field_name="location__name", lookup_expr="icontains", label="Facility")
	class Meta:
		model = VerbalAutopsy
		fields = []
