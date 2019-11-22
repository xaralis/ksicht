from functools import partial

from crispy_forms.helper import FormHelper
from django import forms
from django.template.defaultfilters import filesizeformat
from django.urls import reverse

from ksicht.bulma.forms import FileField
from ksicht.bulma.layout import Field, Layout, Submit
from . import widgets


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


class SolutionSubmitForm(forms.Form):
    SOLUTION_MAX_UPLOAD_SIZE = 1024 * 1024 * 2  # 2MB
    # Add to your settings file
    SOLUTION_CONTENT_TYPES = ["application/pdf"]

    def __init__(self, *args, tasks, **kwargs):
        super().__init__(*args, **kwargs)

        layout_fields = []

        def _clean_file(self, field_name):
            file = self.cleaned_data[field_name]

            if not file:
                return file

            if file.content_type not in self.SOLUTION_CONTENT_TYPES:
                raise forms.ValidationError("Vybere prosím soubor ve formátu PDF.")

            if file.size > self.SOLUTION_MAX_UPLOAD_SIZE:
                raise forms.ValidationError(
                    f"Maximální velikost souboru je {filesizeformat(self.SOLUTION_MAX_UPLOAD_SIZE)}. Vybraný soubor má velikost {filesizeformat(file.size)}."
                )

            return file

        for task in tasks:
            self.fields[f"file_{task.nr}"] = FileField(
                label=f"Vyberte soubor s řešením úlohy č. {task.nr} „{task.title}“",
                required=False,
                allow_empty_file=False,
            )
            layout_fields.append(Field(f"file_{task.nr}"))

            setattr(
                self,
                f"clean_file_{task.nr}",
                partial(_clean_file, self=self, field_name=f"file_{task.nr}"),
            )

        layout_fields.append(
            Submit("submit", "Odeslat", css_class="is-large has-margin-t-xl"),
        )

        self.helper = FormHelper()
        self.helper.layout = Layout(*layout_fields)
        self.helper.form_action = reverse("core:solution_submit")


class SubmissionForm(forms.Form):
    def __init__(self, *args, participant, submitted_digitally, tasks, **kwargs):
        super().__init__(*args, **kwargs)

        self.participant_obj = participant
        self.fields["participant"] = forms.IntegerField(widget=forms.HiddenInput)

        for t in tasks:
            self.fields[f"task_{t.id}"] = forms.BooleanField(
                required=False, disabled=submitted_digitally
            )


class SubmissionOverviewFormSet(forms.BaseFormSet):
    def get_form_kwargs(self, index):
        return self.form_kwargs.get(str(index))


class ScoringForm(forms.ModelForm):
    class Meta:
        class ApplicationModelChoiceField(forms.ModelChoiceField):
            widget = widgets.CurrentChoiceRendererWidget

            def label_from_instance(self, obj):
                return obj.participant.get_full_name()

        field_classes = {"application": ApplicationModelChoiceField}

    def __init__(self, *args, max_score, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["score"] = forms.DecimalField(
            label="", max_value=max_score, min_value=0, max_digits=5, decimal_places=2
        )
