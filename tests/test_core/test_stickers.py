from datetime import datetime
from decimal import Decimal
from uuid import uuid4

import pytest

from ksicht.core import models
from ksicht.core.stickers import resolvers


pytestmark = [pytest.mark.django_db]

tid1 = str(uuid4())
tid2 = str(uuid4())
tid3 = str(uuid4())
tid4 = str(uuid4())


s1 = models.GradeSeries(id="abcd", submission_deadline=datetime(2020, 1, 1, 0, 0))
s2 = models.GradeSeries(id="dcba", submission_deadline=datetime(2020, 3, 1, 0, 0))

t1 = models.Task(id=tid1, points=Decimal("10.00"))
t2 = models.Task(id=tid2, points=Decimal("10.00"))
t3 = models.Task(id=tid3, points=Decimal("10.00"))
t4 = models.Task(id=tid4, points=Decimal("10.00"))

sub1 = models.TaskSolutionSubmission(task_id=tid1)
sub2 = models.TaskSolutionSubmission(task_id=tid2)
sub3 = models.TaskSolutionSubmission(task_id=tid3)
sub4 = models.TaskSolutionSubmission(task_id=tid4)


@pytest.mark.parametrize(
    "context, result",
    (
        (
            {
                "current_series": s1,
                "tasks_in_series": {s1: (t1, t2, t3), s2: (t4,)},
                "submissions": {
                    "by_series": {
                        s1: (sub1, sub2, sub3),
                        s2: (),
                    }
                },
            },
            True,
        ),
        (
            {
                "current_series": s2,
                "tasks_in_series": {s1: (t1, t2, t3), s2: (t4,)},
                "submissions": {
                    "by_series": {
                        s1: (),
                        s2: (sub4,),
                    }
                },
            },
            True,
        ),
        (
            {
                "current_series": s1,
                "tasks_in_series": {s1: (t1, t2, t3), s2: (t4,)},
                "submissions": {
                    "by_series": {
                        s1: (),
                        s2: (),
                    }
                },
            },
            False,
        ),
        (
            {
                "current_series": s1,
                "tasks_in_series": {s1: (), s2: ()},
                "submissions": {
                    "by_series": {
                        s1: (),
                        s2: (),
                    }
                },
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
        (
            {
                "is_last_series": True,
                "submissions": {
                    "by_series": {
                        s1: (sub1,),
                        s2: (sub2,),
                    }
                },
            },
            True,
        ),
        (
            {
                "is_last_series": False,
                "submissions": {
                    "by_series": {
                        s1: (sub1,),
                        s2: (sub2,),
                    }
                },
            },
            False,
        ),
        (
            {
                "is_last_series": True,
                "submissions": {
                    "by_series": {
                        s1: (),
                        s2: (sub1,),
                    }
                },
            },
            False,
        ),
        (
            {
                "is_last_series": True,
                "submissions": {
                    "by_series": {
                        s1: (),
                        s2: (),
                    }
                },
            },
            False,
        ),
    ),
)
def test_solution_in_every_series(context, result):
    assert resolvers.solution_in_every_series(context) is result


@pytest.mark.parametrize(
    "context, result",
    (
        (
            {"is_last_series": True, "submissions": {"by_tasks": {t1: sub1, t1: sub2}}},
            True,
        ),
        (
            {
                "is_last_series": False,
                "submissions": {"by_tasks": {t1: sub1, t1: sub2}},
            },
            False,
        ),
        (
            {"is_last_series": True, "submissions": {"by_tasks": {t1: None, t2: sub1}}},
            False,
        ),
        (
            {"is_last_series": True, "submissions": {"by_tasks": {t1: None, t2: None}}},
            False,
        ),
    ),
)
def test_solved_all_tasks(context, result):
    assert resolvers.solved_all_tasks(context) is result


@pytest.mark.parametrize(
    "context, result",
    (
        (
            {
                "current_series": s1,
                "submissions": {
                    "by_series": {
                        s1: (),
                        s2: (
                            models.TaskSolutionSubmission(score=Decimal("10.0")),
                            models.TaskSolutionSubmission(score=Decimal("5.0")),
                            models.TaskSolutionSubmission(score=Decimal("0.1")),
                        ),
                    }
                },
            },
            False,
        ),
        (
            {
                "current_series": s2,
                "submissions": {
                    "by_series": {
                        s1: (),
                        s2: (
                            models.TaskSolutionSubmission(score=Decimal("10.0")),
                            models.TaskSolutionSubmission(score=Decimal("5.0")),
                            models.TaskSolutionSubmission(score=Decimal("0.1")),
                        ),
                    }
                },
            },
            False,
        ),
        (
            {
                "current_series": s1,
                "submissions": {
                    "by_series": {
                        s1: (
                            models.TaskSolutionSubmission(score=Decimal("0.0")),
                            models.TaskSolutionSubmission(score=Decimal("0.1")),
                        ),
                        s2: (),
                    }
                },
            },
            True,
        ),
        (
            {
                "current_series": s2,
                "submissions": {
                    "by_series": {
                        s1: (
                            models.TaskSolutionSubmission(score=Decimal("0.0")),
                            models.TaskSolutionSubmission(score=Decimal("0.1")),
                        ),
                        s2: (),
                    }
                },
            },
            False,
        ),
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
                        models.TaskSolutionSubmission(score=Decimal("10.0")),
                        models.TaskSolutionSubmission(score=Decimal("5.0")),
                        models.TaskSolutionSubmission(score=None),
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
                        models.TaskSolutionSubmission(score=None),
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
                "current_series": s1,
                "tasks": (t1, t2),
                "submissions": {
                    "by_series": {
                        s1: (
                            models.TaskSolutionSubmission(
                                task=t1, score=Decimal("5.0")
                            ),
                            models.TaskSolutionSubmission(task=t2, score=None),
                        )
                    }
                },
            },
            False,
        ),
        (
            {
                "current_series": s2,
                "tasks": (t1, t2),
                "submissions": {
                    "by_series": {
                        s1: (
                            models.TaskSolutionSubmission(
                                task=t1, score=Decimal("10.0")
                            ),
                            models.TaskSolutionSubmission(task=t2, score=None),
                        ),
                        s2: (),
                    }
                },
            },
            False,
        ),
        (
            {
                "current_series": s1,
                "tasks": (t1, t2),
                "submissions": {
                    "by_series": {
                        s1: (
                            models.TaskSolutionSubmission(
                                task=t1, score=Decimal("10.0")
                            ),
                            models.TaskSolutionSubmission(task=t2, score=None),
                        )
                    }
                },
            },
            True,
        ),
        (
            {
                "current_series": s1,
                "tasks": (t1, t2),
                "submissions": {
                    "by_series": {
                        s1: (
                            models.TaskSolutionSubmission(task=t1, score=None),
                            models.TaskSolutionSubmission(
                                task=t2, score=Decimal("10.0")
                            ),
                        )
                    }
                },
            },
            True,
        ),
        (
            {
                "current_series": s1,
                "tasks": (t1, t2),
                "submissions": {
                    "by_series": {
                        s1: (
                            models.TaskSolutionSubmission(
                                task=t1, score=Decimal("10.0")
                            ),
                            models.TaskSolutionSubmission(
                                task=t2, score=Decimal("10.0")
                            ),
                        )
                    }
                },
            },
            True,
        ),
    ),
)
def test_full_score(context, result):
    assert resolvers.full_score(context) is result


@pytest.mark.parametrize(
    "context, result",
    (
        (
            {
                "current_series": s1,
                "applications": ["1", "2", "3", "4", "5"],
                "current_application": "1",
            },
            False,
        ),
        (
            {
                "current_series": s1,
                "applications": ["1", "2", "3", "4", "5"],
                "current_application": "2",
            },
            True,
        ),
        (
            {
                "current_series": s1,
                "applications": ["1", "2", "3", "4", "5"],
                "current_application": "3",
            },
            False,
        ),
        (
            {
                "current_series": s1,
                "applications": ["1", "2", "3", "4", "5"],
                "current_application": "4",
            },
            False,
        ),
        (
            {
                "current_series": s1,
                "applications": ["1", "2", "3", "4", "5"],
                "current_application": "5",
            },
            False,
        ),
        (
            {
                "current_series": s2,
                "applications": ["1", "2", "3", "4", "5"],
                "current_application": "1",
            },
            False,
        ),
        (
            {
                "current_series": s2,
                "applications": ["1", "2", "3", "4", "5"],
                "current_application": "2",
            },
            False,
        ),
        (
            {
                "current_series": s2,
                "applications": ["1", "2", "3", "4", "5"],
                "current_application": "3",
            },
            True,
        ),
        (
            {
                "current_series": s2,
                "applications": ["1", "2", "3", "4", "5"],
                "current_application": "4",
            },
            False,
        ),
        (
            {
                "current_series": s2,
                "applications": ["1", "2", "3", "4", "5"],
                "current_application": "5",
            },
            False,
        ),
    ),
)
def test_random_20_percent(context, result):
    assert resolvers.random_20_percent(context) is result


@pytest.mark.parametrize(
    "context, result",
    (
        (
            {
                "current_series": s1,
                "submissions": {
                    "by_series": {
                        s1: (
                            models.TaskSolutionSubmission(
                                submitted_at=datetime(2019, 12, 10),
                                file="foo.pdf",
                            ),
                            models.TaskSolutionSubmission(
                                submitted_at=datetime(2019, 12, 31, 23),
                                file="foo.pdf",
                            ),
                        )
                    }
                },
            },
            True,
        ),
        (
            {
                "current_series": s1,
                "submissions": {
                    "by_series": {
                        s1: (
                            models.TaskSolutionSubmission(
                                submitted_at=datetime(2019, 12, 10),
                                file=None,
                            ),
                            models.TaskSolutionSubmission(
                                submitted_at=datetime(2019, 12, 31, 23),
                                file=None,
                            ),
                        )
                    }
                },
            },
            False,
        ),
        (
            {
                "current_series": s1,
                "submissions": {
                    "by_series": {
                        s1: (
                            models.TaskSolutionSubmission(
                                submitted_at=datetime(2019, 12, 10)
                            ),
                            models.TaskSolutionSubmission(
                                submitted_at=datetime(2019, 12, 31, 19, 59)
                            ),
                        )
                    }
                },
            },
            False,
        ),
    ),
)
def test_late_submission(context, result):
    assert resolvers.late_submission(context) is result


@pytest.mark.parametrize(
    "context, result",
    (
        (
            {
                "current_series": s1,
                "submissions": {
                    "by_series": {
                        s1: (
                            models.TaskSolutionSubmission(
                                submitted_at=datetime(2019, 12, 1)
                            ),
                            models.TaskSolutionSubmission(
                                submitted_at=datetime(2019, 12, 13, 23)
                            ),
                        )
                    }
                },
            },
            True,
        ),
        (
            {
                "current_series": s1,
                "submissions": {
                    "by_series": {
                        s1: (
                            models.TaskSolutionSubmission(
                                submitted_at=datetime(2019, 12, 10)
                            ),
                            models.TaskSolutionSubmission(
                                submitted_at=datetime(2019, 12, 31, 19, 59)
                            ),
                        )
                    }
                },
            },
            False,
        ),
    ),
)
def test_early_submission(context, result):
    assert resolvers.early_submission(context) is result


@pytest.mark.parametrize(
    "context, result",
    (
        ({"rank": 10}, False),
        ({"rank": 7}, True),
        ({"rank": 1}, True),
    ),
)
def test_ranked_no_worse_than_7th(context, result):
    assert resolvers.ranked_no_worse_than_7th(context) is result


@pytest.mark.parametrize(
    "context, result",
    (
        ({"rank": 42}, True),
        ({"rank": 7}, False),
        ({"rank": 1}, False),
        ({"rank": 43}, False),
    ),
)
def test_ranked_42nd(context, result):
    assert resolvers.ranked_42nd(context) is result


@pytest.mark.parametrize(
    "context, result",
    (
        ({"is_last_series": True, "score": 10, "max_score": 20, "rank": 35}, True),
        ({"is_last_series": True, "score": 5, "max_score": 20, "rank": 15}, True),
        ({"is_last_series": False, "score": 20, "max_score": 20, "rank": 15}, False),
    ),
)
def test_successful_solver(context, result):
    assert resolvers.successfull_solver(context) is result


@pytest.mark.parametrize(
    "context, result",
    (
        (
            {
                "is_last_series": True,
                "current_series": s1,
                "submissions": {"by_series": {s1: (sub1, sub2)}},
            },
            True,
        ),
        (
            {
                "is_last_series": True,
                "current_series": s1,
                "submissions": {"by_series": {s1: ()}},
            },
            False,
        ),
        (
            {
                "is_last_series": False,
                "current_series": s1,
                "submissions": {"by_series": {s1: (sub1, sub2)}},
            },
            False,
        ),
    ),
)
def test_submitted_solution_in_last_series(context, result):
    assert resolvers.submitted_solution_in_last_series(context) is result
