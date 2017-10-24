from django import forms
from .models import Flow


class QualityChoice(forms.Form):
    choice_field = forms.ChoiceField(widget=forms.RadioSelect,
                                     choices=Flow.quality_choices)
