from datetime import timedelta
from decimal import Decimal
import math
import random

from . import registry


def sticker(sticker_nr):
    def decorator(resolver_fn):
        registry.register(sticker_nr, resolver_fn)
        return resolver_fn

    return decorator


@sticker(1)
def solver(context):
    """Given to anyone who participates."""
    return True


@sticker(2)
def solved_all_tasks_in_series(context):
    """Given to anyone who has submitted solutions for all tasks of a series."""

    def _is_eligible(series, tasks):
        return len(tasks) > 0 and len(
            context["submissions"]["by_series"][series]
        ) == len(tasks)

    return _is_eligible(
        context["current_series"], context["tasks_in_series"][context["current_series"]]
    )


@sticker(3)
def solution_in_every_series(context):
    """Given to anyone who has submitted a solution in every series."""
    return context["is_last_series"] and all(
        len(submissions) != 0
        for submissions in context["submissions"]["by_series"].values()
    )


@sticker(4)
def solved_all_tasks(context):
    """Given to anyone who has submitted solutions for every task."""
    return context["is_last_series"] and all(
        sub is not None for sub in context["submissions"]["by_tasks"].values()
    )


@sticker(8)
def zero_points(context):
    """Given to anyone who has been given 0 score points in any of the submitted solutions within a series."""
    return any(
        sub.score == Decimal("0")
        for sub in context["submissions"]["by_series"][context["current_series"]]
    )


@sticker(9)
def reached_100(context):
    """Given to anyone who has reached a sum of at least 100 points."""
    return sum(
        sub.score or Decimal("0") for sub in context["submissions"]["all"]
    ) >= Decimal("100")


@sticker(10)
def reached_150(context):
    """Given to anyone who has reached a sum of at least 150 points."""
    return sum(
        sub.score or Decimal("0") for sub in context["submissions"]["all"]
    ) >= Decimal("150")


@sticker(12)
def full_score(context):
    """Given to anyone who has been given the maximum number of points for at least one of their submissions within a series."""

    def _is_eligible(submission):
        task = next(t for t in context["tasks"] if submission.task_id == t.pk)
        return task.points == submission.score

    return any(
        _is_eligible(sub)
        for sub in context["submissions"]["by_series"][context["current_series"]]
    )


@sticker(13)
def random_20_percent(context):
    """Randomly (yet with predictable seed according to current_series) given to approx 20% of the applications."""
    applications_count = len(context["applications"])
    pick_count = math.ceil(applications_count * 0.2)

    # Initialize seed for the randomness to be consistent with current_series
    random.seed(context["current_series"].pk)

    return context["current_application"] in random.choices(
        context["applications"], k=pick_count
    )


@sticker(14)
def late_submission(context):
    """Given to anyone who has submitted a solution in series less than 4 hours before submission deadline via this web app."""

    def _is_eligible(submission):
        ## Only when file is provided, e.g. was submitted digitally
        return bool(submission.file) and (
            context["current_series"].submission_deadline - submission.submitted_at
        ) <= timedelta(hours=4)

    return any(
        _is_eligible(sub)
        for sub in context["submissions"]["by_series"][context["current_series"]]
    )


@sticker(15)
def early_submission(context):
    """Given to anyone who has submitted a solution in series more than 2 weeks before submission deadline."""

    def _is_eligible(submission):
        return (
            context["current_series"].submission_deadline - submission.submitted_at
        ) >= timedelta(days=14)

    return all(
        _is_eligible(sub)
        for sub in context["submissions"]["by_series"][context["current_series"]]
    )


@sticker(18)
def ranked_no_worse_than_7th(context):
    """Given to anyone who has ranked no worse than 7th in the series."""
    return context["rank"] <= 7


@sticker(19)
def successfull_solver(context):
    """Given to anyone who has got at least 50% of the points or has ranked 30th or less in the last series."""
    return context["is_last_series"] and (
        (context["score"] >= context["max_score"] * 0.5) or (context["rank"] <= 30)
    )


@sticker(29)
def submitted_solution_in_last_series(context):
    """Given to anyone who has submitted a solution in last series of the grade."""
    return (
        context["is_last_series"]
        and len(context["submissions"]["by_series"][context["current_series"]]) > 0
    )


@sticker(42)
def ranked_42nd(context):
    """Given to anyone who has ranked 42nd in the current series."""
    return context["rank"] == 42
