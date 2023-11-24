from typing import List, Set, Tuple

from . import registry, types
from .. import models


def resolve_stickers(context: types.StickerContext):
    """Get set of stickers where provided context resolves truthy."""
    entitled_to: Set[int] = set()

    for sticker_nr, sticker_resolver in registry.get_all():
        if sticker_resolver(context):
            entitled_to.add(sticker_nr)

    return entitled_to


def _grade_details(grade: models.Grade) -> types.GradeDetails:
    """Get details of the grade."""
    applications = list(
        grade.applications.order_by("created_at").select_related("participant__user")
    )
    series = list(
        models.GradeSeries.objects.filter(grade=grade)
        .select_related("grade")
        .prefetch_related("grade__applications")
    )
    tasks = list(models.Task.objects.filter(series__grade=grade))
    submitted_solutions = models.TaskSolutionSubmission.objects.filter(
        task__series__grade=grade
    ).select_related("task__series")

    rankings_by_series = {
        s: s.get_rankings(
            _applications_cache=applications,
            _tasks_cache=[t for t in tasks if t.series_id == s.pk],
            _submissions_cache=[sol for sol in submitted_solutions],
        )
        for s in series
    }

    def _series_details(
        series: models.GradeSeries, application: models.GradeApplication
    ) -> types.SeriesDetails:
        rankings = rankings_by_series[series]
        application_ranking = next(
            row for row in rankings["listing"] if row[0].pk == application.pk
        )
        return {
            "rank": application_ranking[1],
            "score": application_ranking[3],
            "max_score": rankings["max_score"],
        }

    grade_details: types.GradeDetails = {
        "series": series,
        "tasks": {s: [t for t in tasks if t.series_id == s.pk] for s in series},
        "by_participant": {},
    }

    for application in applications:
        submissions = [
            s for s in submitted_solutions if s.application_id == application.pk
        ]

        grade_details["by_participant"][application.participant] = {
            "series": {s: _series_details(s, application) for s in series},
            "submissions": {
                "all": submissions,
                "by_series": {
                    s: list(sub for sub in submissions if sub.task.series_id == s.pk)
                    for s in series
                },
                "by_tasks": {
                    t: next((sub for sub in submissions if sub.task_id == t.pk), None)
                    for t in tasks
                },
            },
        }

    return grade_details


def get_eligibility(current_series: models.GradeSeries):
    """Find out sticker eligibility for every participant in the series."""

    current_grade = current_series.grade
    grades = [current_grade]
    grades.extend(
        models.Grade.objects.filter(start_date__lt=current_grade.start_date).order_by(
            "-end_date"
        )[:3]
    )
    applications: List[models.GradeApplication] = list(
        current_grade.applications.select_related("participant__user")
    )
    base_context = {
        "by_grades": {grades.index(grade): _grade_details(grade) for grade in grades}
    }
    eligibility: List[Tuple[models.GradeApplication, Set[int]]] = []
    current_grade_details = base_context["by_grades"][0]

    for application in applications:
        context: types.StickerContext = {
            "participant": application.participant,
            "current": {
                "participant": current_grade_details["by_participant"][
                    application.participant
                ],
                "grade": current_grade_details,
                "series": current_series,
                "is_last_series": len(current_grade_details["series"]) > 0
                and current_series == current_grade_details["series"][-1],
            },
            **base_context,
        }

        eligibility.append((application, resolve_stickers(context)))

    return eligibility
