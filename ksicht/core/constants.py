import csv
import os

from django.conf import settings


SCHOOLS = ()

SCHOOLS_CHOICES = (("--jiná--", "-- jiná --"),)

with open(
    os.path.join(settings.BASE_DIR, "fixtures", "schools.csv"), encoding="utf8"
) as schools_file:
    csv_reader = csv.reader(schools_file, delimiter=";")

    for idx, row in enumerate(csv_reader):
        if idx != 0:
            SCHOOLS += (tuple(row),)
            SCHOOLS_CHOICES += (
                (
                    row[0],
                    row[7],
                ),
            )
