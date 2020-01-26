import csv
import os

from django.conf import settings


SCHOOLS = (
    ("--jiná--", "-- jiná --"),
)

with open(os.path.join(settings.BASE_DIR, "fixtures", "schools.csv")) as schools_file:
    csv_reader = csv.reader(schools_file, delimiter=";")
    SCHOOLS += tuple((row[0], row[7]) for idx, row in enumerate(csv_reader) if idx != 0)
