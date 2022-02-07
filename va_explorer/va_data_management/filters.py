from django import forms
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.forms import Select, TextInput
from django_filters import BooleanFilter, CharFilter, DateFilter, FilterSet

from .models import VerbalAutopsy

TRUE_FALSE_CHOICES = (
    (False, "No"),
    (True, "Yes"),
)


def validate_integer(value):
    if not value.isdigit():
        raise ValidationError(
            ("%(value)s is invalid or negative. Please enter only numbers"),
            params={"value": value},
        )


class DateInput(forms.DateInput):
    input_type = "date"


class VAFilter(FilterSet):
    id = CharFilter(
        field_name="id",
        label="ID",
        validators=[validate_integer],
        widget=TextInput(attrs={"class": "form-text"}),
    )
    interviewer = CharFilter(
        field_name="Id10010",
        lookup_expr="icontains",
        label="Interviewer",
        widget=TextInput(attrs={"class": "form-text"}),
    )
    deceased = CharFilter(
        method="filter_deceased",
        label="Deceased",
        widget=TextInput(attrs={"class": "form-text"}),
    )
    start_date = DateFilter(
        field_name="Id10023",
        lookup_expr="gte",
        label="Earliest Date",
        widget=DateInput(attrs={"class": "form-date datepicker"}),
    )
    end_date = DateFilter(
        field_name="Id10023",
        lookup_expr="lte",
        label="Latest Date",
        widget=DateInput(attrs={"class": "form-date datepicker"}),
    )
    location = CharFilter(
        field_name="location__name",
        lookup_expr="icontains",
        label="Facility",
        widget=TextInput(attrs={"class": "form-text"}),
    )
    cause = CharFilter(
        field_name="causes__cause",
        lookup_expr="icontains",
        label="Cause",
        widget=TextInput(attrs={"class": "form-text"}),
    )
    only_errors = BooleanFilter(
        method="filter_errors",
        label="Only Errors",
        widget=Select(choices=TRUE_FALSE_CHOICES, attrs={"class": "custom-select"}),
    )

    class Meta:
        model = VerbalAutopsy
        fields = []

    def filter_deceased(self, queryset, name, value):
        if value:
            return queryset.filter(
                Q(Id10017__icontains=value) | Q(Id10018__icontains=value)
            )
        return queryset

    def filter_errors(self, queryset, name, value):
        if value:
            return queryset.filter(coding_issues__severity="error")
        return queryset
