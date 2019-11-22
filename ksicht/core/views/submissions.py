from collections import OrderedDict
from functools import reduce
from operator import or_

from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.db import models, transaction
from django.forms import formset_factory, modelformset_factory
from django.http.response import HttpResponseNotFound
from django.shortcuts import redirect
from django.utils.decorators import method_decorator
from django.views.generic.edit import FormView
import pydash as py_

from .. import forms
from ..models import Grade, GradeApplication, Participant, Task, TaskSolutionSubmission
from .decorators import current_grade_exists, is_participant
from .helpers import CurrentGradeMixin


__all__ = (
    "SolutionSubmitView",
    "SubmissionOverview",
    "ScoringView",
)


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


@method_decorator(
    [permission_required("change_solution_submission_presence")], name="dispatch"
)
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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["grade"] = self.grade
        return context

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


@method_decorator([permission_required("scoring")], name="dispatch")
class ScoringView(FormView):
    template_name = "core/scoring.html"
    form_class = modelformset_factory(
        TaskSolutionSubmission,
        form=forms.ScoringForm,
        fields=("id", "application", "score"),
        extra=0,
    )

    def dispatch(self, *args, task_id, **kwargs):
        self.task = (
            Task.objects.filter(id=task_id).select_related("series__grade").first()
        )

        if not self.task:
            return HttpResponseNotFound()

        return super().dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["task"] = self.task
        return context

    def get_form_kwargs(self):
        return {
            **super().get_form_kwargs(),
            "queryset": TaskSolutionSubmission.objects.filter(
                task=self.task
            ).select_related("application__participant__user"),
            "form_kwargs": {"max_score": self.task.points},
        }

    def form_valid(self, form):
        form.save()

        messages.add_message(
            self.request,
            messages.SUCCESS,
            "<i class='fas fa-check-circle notification-icon'></i> Bodování bylo uloženo.",
        )

        return redirect(".")
