from datetime import date
import uuid

from psycopg2.extras import DateRange
from cuser.models import AbstractCUser
from django.contrib.postgres.fields import DateRangeField
from django.db import models
from django import forms

from .constants import SCHOOLS


class User(AbstractCUser):
    pass


class Participant(models.Model):
    COUNTRY_CHOICES = (
        ("other", "-- jiný --"),
        ("cz", "Česko"),
        ("sk", "Slovensko"),
    )
    GRADE_CHOICES = (
        ("4", "4"),
        ("3", "3"),
        ("2", "2"),
        ("1", "1"),
        ("l", "nižší"),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)

    phone = models.CharField(verbose_name="Telefon", max_length=20, null=True)
    street = models.CharField(verbose_name="Ulice", max_length=100, null=False)
    city = models.CharField(verbose_name="Obec", max_length=100, null=False)
    zip_code = models.CharField(verbose_name="PSČ", max_length=10, null=False)
    country = models.CharField(
        verbose_name="Stát", max_length=10, null=False, choices=COUNTRY_CHOICES
    )

    school = models.CharField(verbose_name="Škola", max_length=80, null=False, choices=SCHOOLS)
    school_year = models.CharField(
        verbose_name="Ročník", max_length=1, null=False, choices=GRADE_CHOICES
    )

    school_alt_name = models.CharField(
        verbose_name="Název školy", max_length=80, null=True
    )
    school_alt_street = models.CharField(
        verbose_name="Ulice školy", max_length=100, null=True
    )
    school_alt_city = models.CharField(
        verbose_name="Obec školy", max_length=100, null=True
    )
    school_alt_zip_code = models.CharField(
        verbose_name="PSČ školy", max_length=10, null=True
    )


def default_grade_school_year():
    current_year = date.today()
    return f"{current_year.year}/{current_year.year + 1}"


def default_grade_valid_through():
    current_year = date.today().year
    return DateRange(date(current_year, 8, 1), date(current_year + 1, 7, 31))


class Grade(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school_year = models.CharField(
        verbose_name="Školní rok", max_length=50, null=False, db_index=True,
        unique=True, default=default_grade_school_year,
    )
    errata = models.TextField(verbose_name="Errata", null=False, blank=True)
    valid_through = DateRangeField(verbose_name="Datum konání", null=False)

    class Meta:
        verbose_name = "Ročník"
        verbose_name_plural = "Ročníky"

    def __str__(self):
        return self.school_year

    def full_clean(self, *args, **kwargs):
        """Validate the grade.

        Make sure 'valid_through' does not overlap."""
        super().full_clean(*args, **kwargs)

        if self.valid_through is not None:
            g = Grade.objects.filter(valid_through__overlap=self.valid_through).exclude(pk=self.pk).first()

            if g:
                raise forms.ValidationError(f"Datum konání se překrývá s ročníkem '{g}'.")


class GradeSeries(models.Model):
    SERIES_CHOICES = (
        ("1", "1."),
        ("2", "2."),
        ("3", "3."),
        ("4", "4."),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    grade = models.ForeignKey(Grade, on_delete=models.PROTECT, related_name="series")
    series = models.CharField(verbose_name="Série", max_length=1, choices=SERIES_CHOICES, null=False, db_index=True)
    submission_deadline = models.DateTimeField(verbose_name="Deadline pro odeslání řešení", null=False)
    task_file = models.FileField(verbose_name="Brožura", upload_to="rocniky/zadani/", null=True, blank=True)

    class Meta:
        unique_together = ("grade", "series")
        verbose_name = "Série"
        verbose_name_plural = "Série"
        ordering = ("grade", "series")

    def __str__(self):
        return f"{self.grade}: {self.series} série"

