from datetime import date

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
