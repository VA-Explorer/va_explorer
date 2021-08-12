from crispy_forms.helper import FormHelper
from django import forms
from django_filters import FilterSet, DateFilter, CharFilter, DateRangeFilter, BooleanFilter

from va_explorer.va_data_management.models import VerbalAutopsy

class DateInput(forms.DateInput):
    input_type = 'date'


class SupervisionFilter(FilterSet):
	interviewer = CharFilter(field_name="username", lookup_expr="icontains", label="Interviewer")
	start_date = DateFilter(field_name="submissiondate", lookup_expr="gte", label="Earliest Date", widget=DateInput(attrs={'class': 'datepicker'}))
	end_date = DateFilter(field_name="submissiondate", lookup_expr="lte", label="Latest Date", widget=DateInput(attrs={'class': 'datepicker'}))
	location = CharFilter(field_name="location__name", lookup_expr="icontains", label="Facility")

	class Meta:
		model = VerbalAutopsy
		fields = []
