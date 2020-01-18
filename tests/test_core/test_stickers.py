from decimal import Decimal

import pytest

from ksicht.core import models
from ksicht.core.stickers import resolvers


pytestmark = [pytest.mark.django_db]


s1 = models.GradeSeries()
s2 = models.GradeSeries()

t1 = models.Task(id="1", points=Decimal("10.00"))
t2 = models.Task(id="2", points=Decimal("10.00"))
t3 = models.Task(id="3", points=Decimal("10.00"))
t4 = models.Task(id="4", points=Decimal("10.00"))

sub1 = models.TaskSolutionSubmission(task_id="1")
sub2 = models.TaskSolutionSubmission(task_id="2")
sub3 = models.TaskSolutionSubmission(task_id="3")
sub4 = models.TaskSolutionSubmission(task_id="4")


@pytest.mark.parametrize(
    "context, result",
    (
        (
            {
                "tasks_in_series": ((s1, (t1, t2, t3)), (s2, (t4,))),
                "submissions": {"by_series": {s1: (sub1, sub2, sub3), s2: (),}},
            },
            True,
        ),
        (
            {
                "tasks_in_series": ((s1, (t1, t2, t3)), (s2, (t4,))),
                "submissions": {"by_series": {s1: (), s2: (sub4,),}},
            },
            True,
        ),
        (
            {
                "tasks_in_series": ((s1, (t1, t2, t3)), (s2, (t4,))),
                "submissions": {"by_series": {s1: (), s2: (),}},
            },
            False,
        ),
    ),
)
def test_solved_all_tasks_in_series(context, result):
    assert resolvers.solved_all_tasks_in_series(context) is result


@pytest.mark.parametrize(
    "context, result",
    (
        ({"submissions": {"by_series": {s1: (sub1,), s2: (sub2,),}}}, True),
        ({"submissions": {"by_series": {s1: (), s2: (sub1,),}}}, False),
        ({"submissions": {"by_series": {s1: (), s2: (),}}}, False),
    ),
)
def test_solution_in_every_series(context, result):
    assert resolvers.solution_in_every_series(context) is result


@pytest.mark.parametrize(
    "context, result",
    (
        ({"submissions": {"by_tasks": {t1: sub1, t1: sub2,}}}, True),
        ({"submissions": {"by_tasks": {t1: None, t2: sub1,}}}, False),
        ({"submissions": {"by_tasks": {t1: None, t2: None,}}}, False),
    ),
)
def test_solved_all_tasks(context, result):
    assert resolvers.solved_all_tasks(context) is result


@pytest.mark.parametrize(
    "context, result",
    (
        (
            {
                "submissions": {
                    "all": (
                        models.TaskSolutionSubmission(score=Decimal("10.0")),
                        models.TaskSolutionSubmission(score=Decimal("5.0")),
                        models.TaskSolutionSubmission(score=Decimal("0.1")),
                    )
                }
            },
            False,
        ),
        (
            {
                "submissions": {
                    "all": (
                        models.TaskSolutionSubmission(score=Decimal("0.0")),
                        models.TaskSolutionSubmission(score=Decimal("0.1")),
                    )
                }
            },
            True,
        ),
        ({"submissions": {"all": ()}}, False),
    ),
)
def test_zero_points(context, result):
    assert resolvers.zero_points(context) is result


@pytest.mark.parametrize(
    "context, result",
    (
        ({"submissions": {"all": ()}}, False),
        (
            {
                "submissions": {
                    "all": (
                        models.TaskSolutionSubmission(score=Decimal("10.0")),
                        models.TaskSolutionSubmission(score=Decimal("5.0")),
                        models.TaskSolutionSubmission(score=Decimal("0.1")),
                    )
                }
            },
            False,
        ),
        (
            {
                "submissions": {
                    "all": (
                        models.TaskSolutionSubmission(score=Decimal("90.0")),
                        models.TaskSolutionSubmission(score=Decimal("50.0")),
                    )
                }
            },
            True,
        ),
    ),
)
def test_reached_100(context, result):
    assert resolvers.reached_100(context) is result


@pytest.mark.parametrize(
    "context, result",
    (
        ({"submissions": {"all": ()}}, False),
        (
            {
                "submissions": {
                    "all": (
                        models.TaskSolutionSubmission(score=Decimal("10.0")),
                        models.TaskSolutionSubmission(score=Decimal("5.0")),
                        models.TaskSolutionSubmission(score=Decimal("0.1")),
                    )
                }
            },
            False,
        ),
        (
            {
                "submissions": {
                    "all": (
                        models.TaskSolutionSubmission(score=Decimal("90.0")),
                        models.TaskSolutionSubmission(score=Decimal("50.0")),
                    )
                }
            },
            False,
        ),
        (
            {
                "submissions": {
                    "all": (
                        models.TaskSolutionSubmission(score=Decimal("90.0")),
                        models.TaskSolutionSubmission(score=Decimal("60.0")),
                    )
                }
            },
            True,
        ),
    ),
)
def test_reached_150(context, result):
    assert resolvers.reached_150(context) is result


@pytest.mark.parametrize(
    "context, result",
    (
        (
            {
                "tasks": (t1, t2),
                "submissions": {
                    "all": (
                        models.TaskSolutionSubmission(
                            task_id="1", score=Decimal("5.0")
                        ),
                    )
                },
            },
            False,
        ),
        (
            {
                "tasks": (t1, t2),
                "submissions": {
                    "all": (
                        models.TaskSolutionSubmission(
                            task_id="1", score=Decimal("10.0")
                        ),
                    )
                },
            },
            True,
        ),
        (
            {
                "tasks": (t1, t2),
                "submissions": {
                    "all": (
                        models.TaskSolutionSubmission(
                            task_id="2", score=Decimal("10.0")
                        ),
                    )
                },
            },
            True,
        ),
        (
            {
                "tasks": (t1, t2),
                "submissions": {
                    "all": (
                        models.TaskSolutionSubmission(
                            task_id="1", score=Decimal("10.0")
                        ),
                        models.TaskSolutionSubmission(
                            task_id="2", score=Decimal("10.0")
                        ),
                    )
                },
            },
            True,
        ),
    ),
)
def test_full_score(context, result):
    assert resolvers.full_score(context) is result
