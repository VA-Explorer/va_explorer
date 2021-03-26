from django import forms
from tempus_dominus.widgets import DatePicker
from .models import VerbalAutopsy
from .model_choices import AgeGroup, YesNoSimilar


class VerbalAutopsyForm(forms.ModelForm):
    submissiondate = forms.DateField(
        label=VerbalAutopsy.submissiondate.field.verbose_name,
        widget=DatePicker(options={'format': "YYYY/MM/DD", 'useCurrent': False}, attrs={'append': 'fas fa-calendar'}),
        required=False,
    )
    Id10009 = forms.ChoiceField(choices=YesNoSimilar.choices, label=VerbalAutopsy.Id10009.field.verbose_name)
    age_group = forms.ChoiceField(choices=AgeGroup.choices, label=VerbalAutopsy.age_group.field.verbose_name)

    class Meta:
        model = VerbalAutopsy
        exclude = ("id", "location")
