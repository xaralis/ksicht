from collections import OrderedDict
from functools import reduce
from operator import or_
import tempfile
from urllib.parse import quote

from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.db import models, transaction
from django.forms import formset_factory, modelformset_factory
from django.http.response import HttpResponse, HttpResponseNotFound
from django.shortcuts import get_object_or_404, redirect
from django.utils.decorators import method_decorator
from django.views import View
from django.views.generic import FormView, TemplateView

from ksicht import pdf
from .. import forms
from ..models import (
    Grade,
    GradeApplication,
    GradeSeries,
    Participant,
    Task,
    TaskSolutionSubmission,
)
from .decorators import current_grade_exists, is_participant


__all__ = (
    "SolutionSubmitView",
    "SubmissionOverview",
    "ScoringView",
    "SolutionExportView",
)


@method_decorator(
    [current_grade_exists, login_required, is_participant], name="dispatch"
)
class SolutionSubmitView(TemplateView):
    template_name = "core/solution_submit.html"

    def dispatch(self, request, *args, **kwargs):
        self.current_grade = Grade.objects.get_current()

        if not self.current_grade:
            return HttpResponseNotFound()

        self.current_series = self.current_grade.get_current_series()

        if not self.current_series:
            return HttpResponseNotFound()

        self.application = GradeApplication.objects.filter(
            participant=self.request.user.participant_profile, grade=self.current_grade,
        ).first()

        if not self.application:
            return HttpResponseNotFound()

        self.series_tasks = self.current_series.tasks.all()

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "current_grade": self.current_grade,
                "current_series": self.current_series,
                "forms": self.get_forms() if "forms" not in kwargs else kwargs["forms"],
            }
        )
        return context

    def get_forms(self):
        task_submissions = {
            submission.task_id: submission
            for submission in TaskSolutionSubmission.objects.filter(
                application=self.application, task__in=self.series_tasks
            )
        }
        form_task_id = self.request.GET.get("task_id")
        return [
            (
                task,
                forms.SolutionSubmitForm(
                    files=self.request.FILES
                    if self.request.method == "POST" and str(task.id) == form_task_id
                    else None,
                    task=task,
                )
                if task.id not in task_submissions
                else None,
                task_submissions.get(task.id),
            )
            for task in self.series_tasks
        ]

    def post(self, request, *args, **kwargs):
        forms = self.get_forms()

        for task, form in forms:
            if form is not None and form.is_valid():
                self.save_solution(task)
                return redirect("core:solution_submit")

        return self.render_to_response(self.get_context_data(forms=forms))

    @transaction.atomic
    def save_solution(self, task):
        """Create new solution submissions for given files."""
        file_descriptor = self.request.FILES.get(f"file_{task.pk}")

        if not file_descriptor:
            raise ValueError("Could not locate file date")

        submission = TaskSolutionSubmission(
            application=self.application, file=file_descriptor, task=task
        )
        submission.save()

        messages.add_message(
            self.request,
            messages.SUCCESS,
            f"<i class='fas fa-check-circle notification-icon'></i> Řešení úlohy {task} bylo <strong>úspěšně odesláno</strong>.",
        )


@method_decorator(
    [permission_required("change_solution_submission_presence")], name="dispatch"
)
class SubmissionOverview(FormView):
    form_class = formset_factory(
        forms.SubmissionForm, formset=forms.SubmissionOverviewFormSet, extra=0
    )
    template_name = "core/manage/submission_overview.html"

    def dispatch(self, *args, grade_id, series_id, **kwargs):
        self.grade = Grade.objects.filter(id=grade_id).first()
        self.series = GradeSeries.objects.filter(grade=self.grade, pk=series_id).first()

        if not self.grade or not self.series:
            return HttpResponseNotFound()

        return super().dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["grade"] = self.grade
        context["series"] = self.series
        return context

    def get_form_kwargs(self):
        participants = Participant.objects.filter(applications__series=self.series)
        tasks = Task.objects.filter(series=self.series)

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
    template_name = "core/manage/scoring.html"
    form_class = modelformset_factory(
        TaskSolutionSubmission,
        form=forms.ScoringForm,
        fields=("id", "application", "score"),
        extra=0,
    )

    def dispatch(self, *args, task_id, **kwargs):
        self.task = get_object_or_404(
            Task.objects.select_related("series__grade"), id=task_id
        )
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


@method_decorator([permission_required("scoring")], name="dispatch")
class SolutionExportView(View):
    def dispatch(self, *args, task_id, **kwargs):
        self.task = get_object_or_404(Task, id=task_id)
        return super().dispatch(*args, **kwargs)

    def get(self, request, *args, **kwargs):
        submitted_solutions = TaskSolutionSubmission.objects.filter(
            task=self.task, file__isnull=False
        ).order_by("application__participant__user__last_name")
        submitted_solutions = [s for s in submitted_solutions if s.file is not None]

        response = HttpResponse(content_type="application/pdf")
        response["Content-Disposition"] = "attachment; filename*=UTF-8''{}.pdf".format(
            quote(str(self.task) + " - export řešení")
        )
        is_duplex = bool(request.GET.get("duplex"))
        normalized_solution_files = []

        for s in submitted_solutions:
            # Ensure all files have even number of pages for simple duplex printing.
            normalized_file = (
                pdf.ensure_even_pages(s.file, tempfile.TemporaryFile())
                if is_duplex
                else s.file
            )
            normalized_solution_files.append(
                pdf.write_label_on_all_pages(
                    f"Řešitel: {s.application.participant.get_full_name()}".encode("utf8"),
                    normalized_file,
                    tempfile.TemporaryFile(),
                )
            )
            normalized_file.close()

        # Join all files in one large batch.
        pdf.concatenate(normalized_solution_files, response)

        # When finished, close the normalized files.
        for f in normalized_solution_files:
            f.close()

        return response
