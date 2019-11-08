from django.contrib.auth.models import User
from django.db import models


class Participant(models.Model):
    COUNTRY_CHOICES = (
        ("other", "--jiný--"),
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

    user = models.OneToOneField(User, on_delete=models.CASCADE)

    phone = models.CharField(verbose_name="Telefon", max_length=20, null=True)
    street = models.CharField(verbose_name="Ulice", max_length=100, null=False)
    city = models.CharField(verbose_name="Obec", max_length=100, null=False)
    zip_code = models.CharField(verbose_name="PSČ", max_length=10, null=False)
    country = models.CharField(
        verbose_name="Stát", max_length=10, null=False, choices=COUNTRY_CHOICES
    )

    school = models.CharField(verbose_name="Škola", max_length=80, null=False)
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
