from . import registry
from .. import models


def resolve_stickers(context):
    """Get set of stickers where provided context resolves truthy."""
    entitled_to = set()

    for sticker_nr, sticker_resolver in registry.get_all():
        if sticker_resolver(context):
            entitled_to.add(sticker_nr)

    return entitled_to


def get_eligibility(current_series):
    """Find out sticker eligibility for every participant in the series."""
    grade = current_series.grade
    applications = grade.applications.all().select_related("participant")
    series = models.GradeSeries.objects.filter(grade=grade)
    tasks = models.Task.objects.filter(series__grade=grade)
    submitted_solutions = models.TaskSolutionSubmission.objects.filter(
        task__series__grade=grade
    ).select_related("task")

    eligibility = []
    all_application_pks = [a.pk for a in applications]
    rankings = current_series.get_rankings()

    for application in applications:
        submissions = [
            s for s in submitted_solutions if s.application_id == application.pk
        ]
        application_ranking = next(
            row for row in rankings["listing"] if row[0].pk == application.pk
        )

        context = {
            "current_series": current_series,
            "current_application": application.pk,
            "applications": all_application_pks,
            "rank": application_ranking[1],
            "score": application_ranking[3],
            "max_score": rankings["max_score"],
            "series": list(series),
            "tasks": list(tasks),
            "tasks_in_series": {
                s: list(t for t in tasks if t.series_id == s.pk) for s in series
            },
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
            len(context["series"]) > 0
            and context["current_series"] == context["series"][-1]
        )

        eligibility.append((application, resolve_stickers(context)))

    return eligibility
