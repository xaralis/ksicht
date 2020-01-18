from . import registry
from .. import models


def resolve_stickers(context):
    """Get set of stickers where provided context resolves truthy."""
    entitled_to = set()

    for sticker_nr, sticker_resolver in registry.get_all():
        if sticker_resolver(context):
            entitled_to.add(sticker_nr)

    return entitled_to


def get_eligibility(grade):
    """Find out sticker eligibility for every application of the grade."""
    applications = grade.applications.all()

    series = models.GradeSeries.objects.filter(grade=grade)
    tasks = models.Task.objects.filter(series__grade=grade)
    submitted_solutions = models.TaskSolutionSubmission.objects.filter(
        task__series__grade=grade
    )

    eligibility = []

    for application in applications:
        submissions = [
            s for s in submitted_solutions if s.application_id == application.pk
        ]

        context = {
            "series": series,
            "tasks": tasks,
            "tasks_in_series": (
                (s, (t for t in tasks if t.series_id == s.pk)) for s in series
            ),
            "submissions": {
                "all": submissions,
                "by_series": {
                    s: (sub for sub in submissions if sub.task.series_id == s.pk)
                    for s in series
                },
                "by_tasks": {
                    t: next((sub for sub in submissions if sub.task_id == t.pk), [None])
                    for t in tasks
                },
            },
        }

        eligibility.append((application, resolve_stickers(context)))

    return eligibility
