from crispy_forms.helper import FormHelper
from django import forms
from django_filters import FilterSet, DateFilter, CharFilter, DateRangeFilter, BooleanFilter

from .models import VerbalAutopsy


TRUE_FALSE_CHOICES = (
    (False, 'No'),
    (True, 'Yes'),
)


class DateInput(forms.DateInput):
    input_type = 'date'


class VAFilter(FilterSet):
	name = CharFilter(field_name="Id10007", lookup_expr="icontains", label="Name")
	start_date = DateFilter(field_name="Id10023", lookup_expr="gte", label="Earliest Date", widget=DateInput(attrs={'class': 'datepicker'}))
	end_date = DateFilter(field_name="Id10023", lookup_expr="lte", label="Latest Date", widget=DateInput(attrs={'class': 'datepicker'}))
	location = CharFilter(field_name="location__name", lookup_expr="icontains", label="Facility")
	only_errors = BooleanFilter(method="filter_errors", label="Only Errors", widget=forms.Select(choices=TRUE_FALSE_CHOICES, attrs={'class': 'custom-select'}))

	class Meta:
		model = VerbalAutopsy
		fields = []

	def filter_errors(self, queryset, name, value):
		if value:
			return queryset.filter(coding_issues__severity='error')
		return queryset
