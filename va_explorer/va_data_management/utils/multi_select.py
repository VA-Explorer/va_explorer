from django import forms
from django.core import exceptions
from django.db import models
from django.utils.text import capfirst


class MultiSelectFormField(forms.MultipleChoiceField):
    """
    This is a port of django-multiselectfield: https://pypi.org/project/django-multiselectfield/
    The relevant logic has been extracted from django-multiselectfield and included
    in this module. MultiSelectField has been updated to subclass models.TextField
    instead of models.CharField. Last updated django-multiselectfield==1.0.1
    """

    widget = forms.CheckboxSelectMultiple

    def __init__(self, *args, **kwargs):
        self.min_choices = kwargs.pop("min_choices", None)
        self.max_choices = kwargs.pop("max_choices", None)
        self.max_length = kwargs.pop("max_length", None)
        self.widget.attrs = {"class": "va-check"}
        super().__init__(*args, **kwargs)
        # TODO: Uncomment if supporting max_length, max_choices, min_choices
        # self.max_length = get_max_length(self.choices, self.max_length)
        # self.validators.append(MaxValueMultiFieldValidator(self.max_length))
        # if self.max_choices is not None:
        #     self.validators.append(MaxChoicesValidator(self.max_choices))
        # if self.min_choices is not None:
        #     self.validators.append(MinChoicesValidator(self.min_choices))


class MultiSelectField(models.TextField):
    """Choice values can not contain commas."""

    def __init__(self, *args, **kwargs):
        self.min_choices = kwargs.pop("min_choices", None)
        self.max_choices = kwargs.pop("max_choices", None)
        super().__init__(*args, **kwargs)
        # TODO: Uncomment if supporting max_length, max_choices, min_choices
        # self.max_length = get_max_length(self.choices, self.max_length)
        # if VERSION <= (4, 1):
        #     self.validators[0] = MaxValueMultiFieldValidator(self.max_length)
        # else:
        #     self.validators.append(MaxValueMultiFieldValidator(self.max_length))
        # if self.min_choices is not None:
        #     self.validators.append(MinChoicesValidator(self.min_choices))
        # if self.max_choices is not None:
        #     self.validators.append(MaxChoicesValidator(self.max_choices))

    def value_to_string(self, obj):
        value = super().value_from_object(obj)
        return self.get_prep_value(value)

    def validate(self, value, model_instance):
        if not self.editable:
            # Skip validation for non-editable fields.
            return
        if self.choices is not None and value not in self.empty_values:
            arr_choices = dict(self.flatchoices).keys()
            for opt_select in value:
                if opt_select not in arr_choices:
                    raise exceptions.ValidationError(
                        self.error_messages["invalid_choice"] % {"value": value}
                    )

        if value is None and not self.null:
            raise exceptions.ValidationError(self.error_messages["null"], code="null")

        if not self.blank and value in self.empty_values:
            raise exceptions.ValidationError(self.error_messages["blank"], code="blank")

    def formfield(self, **kwargs):
        if isinstance(kwargs.get("form_class"), MultiSelectFormField):
            return kwargs.get("form_class")

        defaults = {
            "required": not self.blank,
            "label": capfirst(self.verbose_name),
            "help_text": self.help_text,
            "choices": self.choices,
            "max_length": self.max_length,
            "min_choices": self.min_choices,
            "max_choices": self.max_choices,
        }
        if self.has_default():
            defaults["initial"] = self.get_default()

        defaults.update(kwargs)
        form_class = (
            defaults.pop("form_class", MultiSelectFormField) or MultiSelectFormField
        )

        return form_class(**defaults)

    def get_prep_value(self, value):
        if isinstance(value, str):
            return value
        if value is None:
            return ""
        # It is a list
        try:
            return ",".join(value)
        # LOCAL FORK CUSTOM LOGIC
        except TypeError:
            # Handle cases where value is not iterable (e.g., nan or invalid types)
            return ""

    def to_python(self, value):
        if isinstance(value, list):
            return value
        if not value:
            return []
        # It is a string
        return value.split(",")

    def from_db_value(self, value, expression, connection):
        if value is None:
            return value
        return self.to_python(value)

    def contribute_to_class(self, cls, name):
        super().contribute_to_class(cls, name)
        if self.choices:

            def get_list(obj):
                fieldname = name
                choicedict = dict(self.flatchoices)
                display = []
                if getattr(obj, fieldname):
                    for value in getattr(obj, fieldname):
                        item_display = choicedict.get(value, value)
                        display.append(str(item_display))
                return display

            def get_display(obj):
                return ", ".join(get_list(obj))

            get_display.short_description = self.verbose_name

            setattr(cls, f"get_{self.name}_list", get_list)
            setattr(cls, f"get_{self.name}_display", get_display)
