from django import forms
from django_filters import BooleanFilter, CharFilter, DateFilter, FilterSet

from va_explorer.va_data_management.models import VerbalAutopsy


class DateInput(forms.DateInput):
    input_type = "date"


PIVOT_OPTIONS = (
    ("interviewer", "Interviewer"),
    ("facility", "Facility"),
)


class SupervisionFilter(FilterSet):
    group_col = BooleanFilter(
        method="filter_for_pivot",
        label="Group by: ",
        widget=forms.Select(choices=PIVOT_OPTIONS, attrs={"class": "custom-select"}),
    )
    location = CharFilter(
        field_name="location__name", lookup_expr="icontains", label="Facility"
    )
    start_date = DateFilter(
        field_name="Id10012",
        lookup_expr="gte",
        label="Earliest Date",
        widget=DateInput(attrs={"class": "datepicker"}),
    )
    end_date = DateFilter(
        field_name="Id10012",
        lookup_expr="lte",
        label="Latest Date",
        widget=DateInput(attrs={"class": "datepicker"}),
    )

    class Meta:
        model = VerbalAutopsy
        fields = []

    def filter_for_pivot(self, queryset, name, value):
        if value:
            return queryset.filter(value__isnull=False)
        return queryset
