from operator import attrgetter

from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.db import transaction
from django.shortcuts import redirect
from django.utils.decorators import method_decorator
from django.views.generic.detail import DetailView
from django.views.generic.edit import BaseFormView
from django.views.generic.list import ListView

from .. import forms, models, stickers
from .decorators import current_grade_exists, is_participant


__all__ = (
    "AutoAssignStickersView",
    "CurrentGradeView",
    "CurrentGradeApplicationView",
    "StickerAssignmentOverview",
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

        return redirect("core:current_grade")

    def form_invalid(self, *args, **kwargs):
        return redirect("core:current_grade")


@method_decorator([permission_required("core.auto_assign_stickers")], name="dispatch")
class AutoAssignStickersView(DetailView):
    template_name = "core/manage/auto_assign_stickers.html"
    queryset = models.Grade.objects.all()

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        eligibility = stickers.engine.get_eligibility(data["object"])
        data["eligibility"] = models.sticker_auto_assignment(eligibility)
        return data

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(object=self.object)
        models.sync_sticker_assignment(context["eligibility"])

        messages.add_message(
            self.request,
            messages.SUCCESS,
            f"<i class='fas fa-check-circle notification-icon'></i> Přiřazení nálepek bylo uloženo</strong>.",
        )

        return redirect(".")


@method_decorator([login_required], name="dispatch")
class StickerAssignmentOverview(ListView):
    template_name = "core/manage/sticker_assignment_overview.html"

    def get_queryset(self):
        return (
            models.GradeApplication.objects.filter(grade__pk=self.kwargs["pk"])
            .select_related("participant")
            .prefetch_related("stickers", "solution_submissions__stickers")
        )

    def get_context_data(self, **kwargs):
        data = super().get_context_data(
            grade=models.Grade.objects.get(pk=self.kwargs["pk"]), **kwargs
        )

        def _collect_stickers(application):
            stickers = set(application.stickers.all())

            for s in application.solution_submissions.all():
                stickers = stickers.union(set(s.stickers.all()))

            return sorted(stickers, key=attrgetter("nr"))

        data["results"] = {a: _collect_stickers(a) for a in data["object_list"]}
        return data
