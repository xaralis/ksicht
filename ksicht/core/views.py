from operator import or_
from django.db import models, transaction
from functools import reduce
from collections import OrderedDict
from django.forms import formset_factory
from django.shortcuts import redirect
from django.http.response import HttpResponseNotFound
from django.views.generic import TemplateView
from django.views.generic.edit import FormView, BaseFormView
from django.views.generic.detail import DetailView

import pydash as py_

from . import forms
from .models import Task, Grade, Participant, GradeApplication, TaskSolutionSubmission
from .decorators import is_participant, current_grade_exists

from django.contrib import messages
from django.contrib.auth.decorators import login_required

from django.utils.decorators import method_decorator


def get_current_grade_context(user):
    context = {}
    context["current_grade"] = current_grade = Grade.objects.get_current()
    context["current_series"] = (
        current_grade.get_current_series() if current_grade else None
    )
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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if self.is_dashboard:
            context["grades"] = Grade.objects.all()[:5]

        return context


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


@method_decorator(
    [current_grade_exists, login_required, is_participant], name="dispatch"
)
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


@method_decorator(
    [current_grade_exists, login_required, is_participant], name="dispatch"
)
class SolutionSubmitView(CurrentGradeMixin, FormView):
    form_class = forms.SolutionSubmitForm
    template_name = "core/solution_submit.html"

    def get_application(self, current_grade):
        return GradeApplication.objects.filter(
            participant=self.request.user.participant_profile, grade=current_grade,
        ).first()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        application = self.get_application(context["current_grade"])

        # User can only submit if there are not submissions yet.
        context["can_submit"] = (
            application is not None and not application.solution_submissions.exists()
        )

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
            messages.add_message(
                self.request,
                messages.WARNING,
                "Žádné soubory s řešením <strong>nebyly odeslány</strong>.",
            )
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
                application=application, file=file_descriptor, task=task
            )
            submission.save()

            messages.add_message(
                self.request,
                messages.SUCCESS,
                "<i class='fas fa-check-circle notification-icon'></i> Vaše řešení úloh bylo <strong>úspěšně odesláno</strong>.",
            )

        return redirect("core:current_grade")


class SubmissionOverview(FormView):
    form_class = formset_factory(
        forms.SubmissionForm, formset=forms.SubmissionOverviewFormSet, extra=0
    )
    template_name = "core/submission_overview.html"

    def dispatch(self, *args, grade_id, **kwargs):
        self.grade = Grade.objects.filter(id=grade_id).first()

        if not self.grade:
            return HttpResponseNotFound()

        return super().dispatch(*args, **kwargs)

    def get_form_kwargs(self):
        participants = Participant.objects.filter(applications=self.grade)
        tasks = Task.objects.filter(series__grade=self.grade)

        submission_map = {}

        for participant in participants:
            submission_map[participant.user_id] = OrderedDict()

            for task in tasks:
                submission_map[participant.user_id][task.id] = None

        for s in TaskSolutionSubmission.objects.filter(
            application__grade=self.grade
        ).select_related("task"):
            submission_map[s.application.participant_id][s.task.id] = s

        def _build_initial(participant):
            i = {"participant": participant.user_id}

            for task_id, submission in submission_map[participant.user_id].items():
                i[f"task_{task_id}"] = bool(submission)

            return i

        return {
            **super().get_form_kwargs(),
            "initial": {
                i: _build_initial(participant)
                for i, participant in enumerate(participants)
            },
            "form_kwargs": {
                str(i): {
                    "participant": participant,
                    "submitted_digitally": any(
                        (bool(s) and bool(s.file))
                        for s in submission_map[participant.user_id].values()
                    ),
                    "tasks": tasks,
                }
                for i, participant in enumerate(participants)
            },
        }

    def form_valid(self, form):
        submissions = TaskSolutionSubmission.objects.filter(
            application__grade=self.grade
        )
        applications = GradeApplication.objects.filter(grade=self.grade)

        # Map participant_id -> application_id
        application_map = {a.participant_id: str(a.id) for a in applications}

        # Saved submssions come from DB, triplets (application_id, task_id, should_exist)
        saved_submissions = {
            (application_map[s.application.participant_id], str(s.task_id), True)
            for s in submissions
        }
        desired_submissions = set()

        for cdi in form.cleaned_data:
            participant_id = cdi["participant"]

            for field_name, field_value in cdi.items():
                if field_name != "participant":
                    _, task_id = field_name.split("_")
                    desired_submissions.add(
                        (application_map[participant_id], task_id, field_value)
                    )

        missing_submissions = desired_submissions - saved_submissions
        overdue_submissions = saved_submissions - desired_submissions

        to_create = []
        to_remove = []

        # Handle submissions to create
        for s in missing_submissions:
            app_id, task_id, should_exist = s

            if should_exist:
                to_create.append(
                    TaskSolutionSubmission(application_id=app_id, task_id=task_id)
                )

        TaskSolutionSubmission.objects.bulk_create(to_create)

        # Handle submissions to delete
        filtering = []
        for s in overdue_submissions:
            app_id, task_id, _ = s
            filtering.append(models.Q(application_id=app_id, task_id=task_id))

        if len(filtering) > 0:
            TaskSolutionSubmission.objects.filter(reduce(or_, filtering)).delete()

        messages.add_message(
            self.request,
            messages.SUCCESS,
            "<i class='fas fa-check-circle notification-icon'></i> Odevzdaná řešení byla uložena.",
        )

        return redirect(".")
