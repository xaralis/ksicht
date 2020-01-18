from decimal import Decimal

from . import registry


def sticker(sticker_nr):
    def wrapped(resolver_fn):
        return resolver_fn

    registry.register(sticker_nr, wrapped)

    return wrapped


@sticker(1)
def solver(context):
    """Given to anyone who participates."""
    return True


@sticker(2)
def solved_all_tasks_in_series(context):
    """Given to anyone who has submitted solutions for all tasks of a series."""

    def _is_eligible(tasks_in_series):
        series, tasks = tasks_in_series
        return len(context["submissions"]["by_series"][series]) == len(tasks)

    return any(
        _is_eligible(tasks_in_series) for tasks_in_series in context["tasks_in_series"]
    )


@sticker(3)
def solution_in_every_series(context):
    """Given to anyone who has submitted a solution in every series."""
    return all(
        len(submissions) != 0
        for submissions in context["submissions"]["by_series"].values()
    )


@sticker(4)
def solved_all_tasks(context):
    """Given to anyone who has submitted solutions for every task."""
    return all(sub is not None for sub in context["submissions"]["by_tasks"].values())


@sticker(8)
def zero_points(context):
    """Given to anyone who has been given 0 score points in any of the submitted solutions."""
    return any(sub.score == Decimal("0") for sub in context["submissions"]["all"])


@sticker(9)
def reached_100(context):
    """Given to anyone who has reached a sum of at least 100 points."""
    return sum(sub.score for sub in context["submissions"]["all"]) >= Decimal("100")


@sticker(10)
def reached_150(context):
    """Given to anyone who has reached a sum of at least 150 points."""
    return sum(sub.score for sub in context["submissions"]["all"]) >= Decimal("150")


@sticker(12)
def full_score(context):
    """Given to anyone who has been given the maximum number of points for at least one of their submissions."""

    def _is_eligible(submission):
        task = next(t for t in context["tasks"] if submission.task_id == t.pk)
        return task.points == submission.score

    return any(_is_eligible(sub) for sub in context["submissions"]["all"])
