from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import redirect, reverse
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView
from django.views.generic.edit import BaseFormView, FormView
from django.views.generic.detail import DetailView

import pydash as py_

from .decorators import is_participant, current_grade_exists
from .models import Grade, GradeApplication, TaskSolutionSubmission
from . import forms


def get_current_grade_context(user):
    context = {}
    context["current_grade"] = current_grade = Grade.objects.get_current()
    context["current_series"] = current_grade.get_current_series() if current_grade else None
    context["is_current_grade_participant"] = (
        current_grade.participants.filter(user=user).exists()
        if current_grade
        else False
    )
    return context


class CurrentGradeMixin:
    def dispatch(self, *args, **kwargs):
        self.grade_context = get_current_grade_context(self.request.user)
        return super().dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(self.grade_context)
        return context


class HomeView(CurrentGradeMixin, TemplateView):
    @property
    def is_dashboard(self):
        return self.request.user.is_authenticated

    def get_template_names(self):
        if self.is_dashboard:
            return ["core/dashboard.html"]
        return "core/home.html"


@method_decorator(current_grade_exists, name="dispatch")
class CurrentGradeView(DetailView):
    template_name = "core/current_grade.html"

    def get_object(self, *args, **kwargs):
        return Grade.objects.get_current()

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data["is_participant"] = (
            self.request.user.is_authenticated and self.request.user.is_participant
        )
        data["is_grade_participant"] = (
            self.request.user.is_authenticated
            and self.object.participants.filter(user=self.request.user).exists()
        )
        data["can_apply"] = data["is_participant"] and not data["is_grade_participant"]
        data["application_form"] = forms.CurrentGradeAppliationForm()
        return data


@method_decorator([current_grade_exists, login_required, is_participant], name="dispatch")
class CurrentGradeApplicationView(BaseFormView):
    form_class = forms.CurrentGradeAppliationForm

    def form_valid(self, *args, **kwargs):
        user = self.request.user

        if not user.is_authenticated:
            return self.form_invalid()

        grade = Grade.objects.get_current()

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


@method_decorator([current_grade_exists, login_required, is_participant], name="dispatch")
class SolutionSubmitView(CurrentGradeMixin, FormView):
    form_class = forms.SolutionSubmitForm
    template_name = "core/solution_submit.html"

    def get_application(self, current_grade):
        return GradeApplication.objects.filter(
            participant=self.request.user.participant_profile,
            grade=current_grade,
        ).first()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        application = self.get_application(context["current_grade"])

        # User can only submit if there are not submissions yet.
        context["can_submit"] = application is not None and not application.solution_submissions.exists()

        return context

    def get_form_kwargs(self):
        current_series = Grade.objects.get_current().get_current_series()

        kwargs = super().get_form_kwargs()
        kwargs["tasks"] = current_series.tasks.all()

        return kwargs

    @transaction.atomic
    def form_valid(self, form):
        """Create new solution submissions for given files."""
        if not self.request.FILES:
            messages.add_message(self.request, messages.WARNING, "Žádné soubory s řešením <strong>nebyly odeslány</strong>.")
            return redirect(".")

        application = self.get_application(self.grade_context["current_grade"])
        tasks = self.grade_context["current_series"].tasks.all()

        def _find_task(file_id):
            return py_.find(tasks, lambda t: t.nr == file_id)

        for file_id, file_descriptor in self.request.FILES.items():
            task = _find_task(file_id.split("_")[1])

            if not task:
                raise ValueError("Could not find proper task")

            submission = TaskSolutionSubmission(
                application=application,
                file=file_descriptor,
                task=task
            )
            submission.save()

            messages.add_message(self.request, messages.SUCCESS, "<i class='fas fa-check-circle notification-icon'></i> Vaše řešení úloh bylo <strong>úspěšně odesláno</strong>.")

        return redirect("core:current_grade")
