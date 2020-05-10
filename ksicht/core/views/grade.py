from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.utils.decorators import method_decorator
from django.views.generic.detail import DetailView
from django.views.generic.edit import BaseFormView

from .. import forms, models
from .decorators import current_grade_exists, is_participant


__all__ = (
    "CurrentGradeView",
    "CurrentGradeApplicationView",
)


@method_decorator(current_grade_exists, name="dispatch")
class CurrentGradeView(DetailView):
    template_name = "core/current_grade.html"

    def get_object(self, *args, **kwargs):
        return models.Grade.objects.get_current()

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data["is_participant"] = (
            self.request.user.is_authenticated and self.request.user.is_participant()
        )
        data["is_grade_participant"] = (
            self.request.user.is_authenticated
            and self.object.participants.filter(user=self.request.user).exists()
        )
        data["can_apply"] = data["is_participant"] and not data["is_grade_participant"]
        data["application_form"] = forms.CurrentGradeAppliationForm()
        return data


@method_decorator(
    [current_grade_exists, login_required, is_participant], name="dispatch"
)
class CurrentGradeApplicationView(BaseFormView):
    form_class = forms.CurrentGradeAppliationForm

    def form_valid(self, *args, **kwargs):
        user = self.request.user

        if not user.is_authenticated:
            return self.form_invalid()

        grade = models.Grade.objects.get_current()

        if not grade:
            return self.form_invalid()

        can_apply = (
            user.is_participant and not grade.participants.filter(user=user).exists()
        )

        if can_apply:
            grade.participants.add(user.participant_profile)

        messages.add_message(
            self.request,
            messages.SUCCESS,
            f"<i class='fas fa-check-circle notification-icon'></i> Přihlášení do KSICHTu proběhlo úspěšně. Hurá na řešení!</strong>.",
        )

        return redirect("core:current_grade")

    def form_invalid(self, *args, **kwargs):
        return redirect("core:current_grade")
