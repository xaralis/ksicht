from functools import partial

from crispy_forms.helper import FormHelper
from django import forms
from django.template.defaultfilters import filesizeformat
from django.urls import reverse
from django_select2.forms import Select2MultipleWidget

from ksicht.bulma.forms import FileField
from ksicht.bulma.layout import Column, Field, Layout, Row, Submit
from . import models, widgets


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

    def __init__(self, *args, task, **kwargs):
        super().__init__(*args, **kwargs)

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

        self.fields[f"file_{task.pk}"] = FileField(
            label="Vyberte soubor s řešením", required=True, allow_empty_file=False,
        )

        setattr(
            self,
            f"clean_file_{task.pk}",
            partial(_clean_file, self=self, field_name=f"file_{task.pk}"),
        )

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column(
                    Field(f"file_{task.pk}"), css_class="is-12-mobile is-10-desktop"
                ),
                Column(
                    Submit("submit", "Odeslat", css_class="is-outlined"),
                    css_class="is-12-mobile is-2-desktop has-text-right-desktop",
                ),
                css_class="is-mobile is-multiline",
            )
        )
        self.helper.form_action = (
            reverse("core:solution_submit") + f"?task_id={task.pk}"
        )


class SubmissionForm(forms.Form):
    def __init__(self, *args, participant, digital_submissions, tasks, **kwargs):
        super().__init__(*args, **kwargs)

        self.participant_obj = participant
        self.fields["participant"] = forms.IntegerField(widget=forms.HiddenInput)

        for t in tasks:
            self.fields[f"task_{t.id}"] = forms.BooleanField(
                required=False, disabled=t.id in digital_submissions
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
            label="",
            max_value=max_score,
            min_value=0,
            max_digits=5,
            decimal_places=2,
            required=False,
        )

        self.fields["stickers"] = forms.ModelMultipleChoiceField(
            queryset=models.Sticker.objects.filter(handpicked=True).order_by("nr"),
            widget=Select2MultipleWidget({"data-width": "100%"}),
            required=False,
        )
