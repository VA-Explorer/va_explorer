from django import forms

from .models import VerbalAutopsy

class VerbalAutopsyForm(forms.ModelForm):

    class Meta:
        model = VerbalAutopsy
        exclude = ('id', 'location')
