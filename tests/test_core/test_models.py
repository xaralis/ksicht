from datetime import date, timedelta

import pytest

from ksicht.core import models


pytestmark = [pytest.mark.django_db]


@pytest.fixture
def sample_grades():
    g1 = models.Grade.objects.create(
        school_year="2009", start_date=date(2009, 4, 11), end_date=date(2009, 12, 31)
    )
    g2 = models.Grade.objects.create(
        school_year="2010", start_date=date(2010, 1, 1), end_date=date(2010, 4, 10)
    )
    g3 = models.Grade.objects.create(
        school_year="2010-2", start_date=date(2010, 4, 11), end_date=date(2011, 4, 10)
    )

    return g1, g2, g3


@pytest.mark.parametrize(
    "current_date, grade",
    (
        (date(2009, 1, 1), None),
        (date(2009, 10, 1), 0),
        (date(2010, 1, 1), 1),
        (date(2010, 3, 1), 1),
        (date(2010, 4, 10), 1),
        (date(2010, 4, 11), 2),
        (date(2012, 1, 1), None),
    ),
)
def test_get_current(sample_grades, current_date, grade):
    result = models.Grade.objects.get_current(current_date)

    if grade is not None:
        assert result == sample_grades[grade]
    else:
        assert result is None


def test_active_in_series():
    u1 = models.User.objects.create(email="u1@example.com")
    u2 = models.User.objects.create(email="u2@example.com")
    u3 = models.User.objects.create(email="u3@example.com")
    u4 = models.User.objects.create(email="u4@example.com")

    p1 = models.Participant.objects.create(user=u1)
    p2 = models.Participant.objects.create(user=u2)
    p3 = models.Participant.objects.create(user=u3)

    today = date.today()

    grade = models.Grade.objects.create(
        school_year="Current",
        start_date=today - timedelta(days=30),
        end_date=today + timedelta(days=30),
    )

    # Prevprev series
    s1 = models.GradeSeries.objects.create(
        grade=grade, series="1", submission_deadline=today - timedelta(days=20)
    )
    # Prev. series
    s2 = models.GradeSeries.objects.create(
        grade=grade, series="2", submission_deadline=today - timedelta(days=10)
    )
    # Current series
    s3 = models.GradeSeries.objects.create(
        grade=grade, series="3", submission_deadline=today + timedelta(days=5)
    )

    # Applied during prevprev series, has submitted a solution
    a1 = models.GradeApplication.objects.create(participant=p1, grade=grade)
    a1.created_at = s1.submission_deadline - timedelta(days=5)
    a1.save()

    t1 = models.Task.objects.create(series=s1, nr="1", points=10)
    models.TaskSolutionSubmission.objects.create(application=a1, task=t1)

    # Applied during prev series
    a2 = models.GradeApplication.objects.create(participant=p2, grade=grade)
    a2.created_at = s2.submission_deadline - timedelta(days=5)
    a2.save()
    # Applied during curr series
    a3 = models.GradeApplication.objects.create(participant=p3, grade=grade)
    a3.created_at = s3.submission_deadline - timedelta(days=5)
    a3.save()

    active_in_series = models.Participant.objects.active_in_series(s3)

    assert sorted(list(active_in_series), key=lambda p: p.user_id) == [p1, p3]
