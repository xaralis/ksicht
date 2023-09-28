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


def get_eligibility(current_series: models.GradeSeries):
    """Find out sticker eligibility for every participant in the series."""
    grade = current_series.grade
    applications = list(grade.applications.select_related("participant__user"))
    series = list(models.GradeSeries.objects.filter(grade=grade))
    tasks = list(models.Task.objects.filter(series__grade=grade))
    submitted_solutions = models.TaskSolutionSubmission.objects.filter(
        task__series__grade=grade
    ).select_related("task")

    eligibility: List[Tuple[models.GradeApplication, Set[int]]] = []
    rankings_by_series = {
        s: s.get_rankings(exclude_submissionless=False) for s in series
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
            "tasks": [t for t in tasks if t.series_id == series.pk],
        }

    for application in applications:
        submissions = [
            s for s in submitted_solutions if s.application_id == application.pk
        ]

        context: types.StickerContext = {
            "current_series": current_series,
            "current_application": application,
            "applications": applications,
            "series": {s: _series_details(s, application) for s in series},
            "all_series": series,
            "tasks": tasks,
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
        context["is_last_series"] = (
            len(context["series"]) > 0 and context["current_series"] == series[-1]
        )

        eligibility.append((application, resolve_stickers(context)))

    return eligibility
