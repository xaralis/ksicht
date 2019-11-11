from django import forms
from django.urls import reverse

from crispy_forms.helper import FormHelper

from ksicht.bulma.layout import Field, Layout, Submit


class CurrentGradeAppliationForm(forms.Form):
    applied = forms.BooleanField(initial="y", required=True, widget=forms.HiddenInput)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Field("applied"),
            Submit("submit", "Přihlásit se do ročníku", css_class="is-small"),
        )
        self.helper.form_action = reverse("core:current_grade_application")
