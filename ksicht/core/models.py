from datetime import date, datetime
from decimal import Decimal
import logging
from operator import attrgetter
import tempfile
import uuid

from cuser.models import AbstractCUser
from django import forms
from django.contrib.auth.models import Group as UserGroup
from django.core.validators import MinValueValidator
from django.core.files.base import File
from django.db import models
from django.urls import reverse
from django.utils.text import slugify
import pydash as py_

from ksicht.pdf import prepare_submission_for_export

from .constants import SCHOOLS_CHOICES

logger = logging.getLogger(__name__)


class User(AbstractCUser):
    def __str__(self):
        return f"{self.get_full_name()} <{self.get_username()}>"

    def is_participant(self):
        return Participant.objects.filter(user=self).exists()


class GradeManager(models.Manager):
    def get_current(self, current=None):
        current_date = current or date.today()
        return self.filter(
            start_date__lte=current_date, end_date__gte=current_date
        ).first()

    def archive(self, current=None):
        current_date = current or date.today()
        return self.filter(end_date__lt=current_date)


def default_grade_school_year():
    current_year = date.today()
    return f"{current_year.year}/{current_year.year + 1}"


def default_grade_start():
    return date(date.today().year, 8, 1)


def default_grade_end():
    return date(date.today().year + 1, 7, 31)


class Grade(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school_year = models.CharField(
        verbose_name="Školní rok",
        max_length=50,
        null=False,
        db_index=True,
        unique=True,
        default=default_grade_school_year,
    )
    errata = models.TextField(verbose_name="Errata", null=False, blank=True)
    start_date = models.DateField(
        verbose_name="Začíná",
        null=False,
        blank=False,
        db_index=True,
        default=default_grade_start,
    )
    end_date = models.DateField(
        verbose_name="Končí",
        null=False,
        blank=False,
        db_index=True,
        default=default_grade_end,
    )

    objects = GradeManager()

    class Meta:
        verbose_name = "Ročník"
        verbose_name_plural = "Ročníky"
        ordering = ("-end_date",)

    @property
    def is_in_progress(self):
        return self.start_date <= date.today() <= self.end_date

    def __str__(self):
        return str(self.school_year)

    def full_clean(self, exclude=None, validate_unique=True):
        """Validate the grade.

        Make sure 'valid_through' does not overlap."""
        super().full_clean(exclude, validate_unique)

        if self.start_date is not None and self.end_date is not None:
            g = (
                Grade.objects.filter(
                    models.Q(
                        start_date__lte=self.start_date,
                        end_date__gte=self.start_date,
                    )
                    | models.Q(
                        start_date__lte=self.end_date,
                        end_date__gte=self.end_date,
                    )
                )
                .exclude(pk=self.pk)
                .first()
            )

            if g:
                raise forms.ValidationError(
                    f"Datum konání se překrývá s ročníkem '{g}'."
                )

    def prefetch_series(self):
        if not hasattr(self, "_prefetched_series"):
            self._prefetched_series = self.series.all().prefetch_related(
                "tasks", "attachments"
            )
        return self._prefetched_series

    def get_current_series(self):
        """Return first series that can still accept solution submissions from participants."""
        return (
            py_.chain(list(self.prefetch_series()))
            .filter(attrgetter("accepts_solution_submissions"))
            .sort(key=attrgetter("submission_deadline"))
            .head()
            .value()
        )

    def get_previous_series(self):
        """Return last series that has been closed.

        This is useful for staff to get what needs to be worked with easily."""
        return (
            py_.chain(list(self.prefetch_series()))
            .filter(lambda s: not s.accepts_solution_submissions)
            .sort(key=attrgetter("submission_deadline"))
            .reverse()
            .head()
            .value()
        )

    def get_future_series(self):
        """Get all future series, e.g. those that will come after the current one."""
        current_series = self.get_current_series()

        if not current_series:
            return []

        return [
            s
            for s in self.prefetch_series()
            if s.submission_deadline > current_series.submission_deadline
        ]


class GradeSeries(models.Model):
    SERIES_CHOICES = (
        ("1", "1."),
        ("2", "2."),
        ("3", "3."),
        ("4", "4."),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    grade = models.ForeignKey(
        Grade, verbose_name="Ročník", on_delete=models.CASCADE, related_name="series"
    )
    series = models.CharField(
        verbose_name="Série",
        max_length=1,
        choices=SERIES_CHOICES,
        null=False,
        db_index=True,
    )
    submission_deadline = models.DateTimeField(
        verbose_name="Deadline pro odeslání řešení", null=False
    )
    task_file = models.FileField(
        verbose_name="Brožura", upload_to="rocniky/zadani/", null=True, blank=True
    )
    results_published = models.BooleanField(
        verbose_name="Zveřejnit výsledky",
        null=False,
        blank=False,
        default=False,
        db_index=True,
    )

    class Meta:
        unique_together = ("grade", "series")
        verbose_name = "Série"
        verbose_name_plural = "Série"
        ordering = ("grade", "series")
        permissions = (
            ("series_task_envelopes_printout", "Export obálek pro školy se zadáním"),
            ("series_solution_envelopes_printout", "Export obálek s řešením"),
        )

    def __str__(self):
        return f"{self.get_series_display()} série"

    def get_absolute_url(self):
        return reverse(
            "core:series_detail", kwargs={"pk": self.pk, "grade_id": self.grade_id}
        )

    @property
    def accepts_solution_submissions(self):
        return self.task_file is not None and self.submission_deadline > datetime.now(
            self.submission_deadline.tzinfo
        )

    def get_rankings(self, exclude_submissionless=True):
        """Calculate results for series.

        Adds detailed task listing for individual series tasks and a grand total with total score so far
        (this series and the previous ones).
        """
        # Only applications with an actual solution submission
        applications = self.grade.applications.select_related(
            "participant__user"
        ).order_by("created_at")

        if exclude_submissionless:
            applications = applications.exclude(solution_submissions=None)

        tasks = self.tasks.all()
        submissions = TaskSolutionSubmission.objects.filter(
            application__grade=self.grade, task__series__series__lte=self.series
        )

        scoring_dict = {
            a: {"by_tasks": {t: None for t in tasks}, "total": Decimal("0")}
            for a in applications
        }

        def _find_application(app_id):
            return py_.find(applications, lambda a: a.pk == app_id)

        def _find_task(task_id):
            return py_.find(tasks, lambda t: t.pk == task_id)

        for s in submissions:
            a = _find_application(s.application_id)
            t = _find_task(s.task_id)

            if t:
                scoring_dict[a]["by_tasks"][t] = s.score

            scoring_dict[a]["total"] += s.score or Decimal("0")

        scoring = [
            (application, scores["by_tasks"], scores["total"])
            for (application, scores) in scoring_dict.items()
        ]

        # Attach ranks
        sorted_scoring = [
            # (application, rank, task scores, total score)
            (row[0], index + 1, row[1], row[2])
            for (index, row) in enumerate(
                sorted(scoring, key=lambda r: r[2], reverse=True)
            )
        ]

        return {
            "max_score": Task.objects.filter(
                series__grade=self.grade, series__series__lte=self.series
            ).aggregate(models.Sum("points"))["points__sum"],
            "listing": sorted_scoring,
        }

    def tasks_with_submission_count(self):
        return self.tasks.all().annotate(
            submission_count=models.Count("solution_submissions")
        )


class GradeSeriesAttachment(models.Model):
    title = models.CharField(verbose_name="Název", max_length=255, null=False)
    file = models.FileField(
        verbose_name="Soubor", upload_to="rocniky/prilohy/", null=False, blank=False
    )
    series = models.ForeignKey(
        GradeSeries,
        verbose_name="Série",
        on_delete=models.CASCADE,
        related_name="attachments",
    )

    class Meta:
        verbose_name = "Příloha série"
        verbose_name_plural = "Přílohy sérií"
        ordering = ("series", "title")

    def __str__(self):
        return str(self.title)


class Task(models.Model):
    NR_CHOICES = (
        ("1", "1."),
        ("2", "2."),
        ("3", "3."),
        ("4", "4."),
        ("5", "5."),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    series = models.ForeignKey(
        GradeSeries,
        verbose_name="Série",
        on_delete=models.PROTECT,
        related_name="tasks",
    )
    nr = models.CharField(
        verbose_name="Číslo úlohy",
        max_length=1,
        choices=NR_CHOICES,
        null=False,
        db_index=True,
    )
    title = models.CharField(verbose_name="Název", max_length=150, null=False)
    points = models.PositiveIntegerField(
        verbose_name="Max. počet bodů",
        null=False,
        blank=False,
        validators=(MinValueValidator(1),),
    )

    class Meta:
        verbose_name = "Úloha"
        verbose_name_plural = "Úlohy"
        ordering = ("series", "nr")
        permissions = (("solution_export", "Export odevzdaných úloh"),)

    def __str__(self):
        return str(self.title)


class ParticipantManager(models.Manager):
    def active_in_series(self, current_series):
        """Return active participants for series.

        - Everyone who has submitted a solution
        - Everyone who has filed a GradeApplication after the previous
          GradeSeries deadline and before the current GradeSeries deadline
        """
        grade = current_series.grade
        grade.prefetch_series()
        grade_series = list(grade.series.all())

        current_series_index = grade_series.index(current_series)

        # All applications in grade with some submission
        applications_with_submission = GradeApplication.objects.filter(
            grade=grade,
        ).exclude(solution_submissions=None)

        # Has applied in this grade and has some submission
        query = models.Q(gradeapplication__in=applications_with_submission)

        if current_series_index != 0:
            previous_series = grade_series[current_series_index - 1]

            # Has applied after previous series
            applications_in_deadline_range = GradeApplication.objects.filter(
                grade=grade,
                created_at__range=(
                    previous_series.submission_deadline,
                    current_series.submission_deadline,
                ),
            )

            query = query | models.Q(
                gradeapplication__in=applications_in_deadline_range
            )

        return self.filter(query).distinct()


class Participant(models.Model):
    COUNTRY_CHOICES = (
        ("other", "-- jiný --"),
        ("cz", "Česko"),
        ("sk", "Slovensko"),
    )
    GRADE_CHOICES = (
        ("4", "4."),
        ("3", "3."),
        ("2", "2."),
        ("1", "1."),
        ("l", "nižší"),
    )

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name="participant_profile",
    )

    phone = models.CharField(verbose_name="Telefon", max_length=20, null=True)
    street = models.CharField(
        verbose_name="Ulice a číslo popisné/orientační", max_length=100, null=False
    )
    city = models.CharField(verbose_name="Obec", max_length=100, null=False)
    zip_code = models.CharField(verbose_name="PSČ", max_length=10, null=False)
    country = models.CharField(
        verbose_name="Stát", max_length=10, null=False, choices=COUNTRY_CHOICES
    )

    school = models.CharField(
        verbose_name="Škola",
        max_length=80,
        null=False,
        choices=SCHOOLS_CHOICES,
    )    
    school_year = models.CharField(
        verbose_name="Ročník",
        max_length=1,
        null=False,
        choices=GRADE_CHOICES,
    )

    school_alt_name = models.CharField(
        verbose_name="Název školy", max_length=80, null=True, blank=True
    )
    school_alt_street = models.CharField(
        verbose_name="Ulice školy", max_length=100, null=True, blank=True
    )
    school_alt_city = models.CharField(
        verbose_name="Obec školy", max_length=100, null=True, blank=True
    )
    school_alt_zip_code = models.CharField(
        verbose_name="PSČ školy", max_length=10, null=True, blank=True
    )

    applications = models.ManyToManyField(
        Grade,
        verbose_name="Přihlášky",
        related_name="participants",
        blank=True,
        through="GradeApplication",
    )

    objects = ParticipantManager()

    class Meta:
        verbose_name = "Řešitel"
        verbose_name_plural = "Řešitelé"

    @property
    def school_name(self):
        return (
            self.get_school_display()
            if self.school != "--jiná--"
            else self.school_alt_name
        )

    def __str__(self):
        return f"Profil účastníka pro <{self.user}>"

    def get_full_name(self):
        return f"{self.user.get_full_name() or self.user.email}"


class GradeApplication(models.Model):
    grade = models.ForeignKey(
        Grade, on_delete=models.CASCADE, related_name="applications"
    )
    participant = models.ForeignKey(Participant, on_delete=models.PROTECT)
    participant_current_grade = models.CharField(
        verbose_name="Ročník",
        max_length=10,
        null=True
    )
    created_at = models.DateTimeField(verbose_name="Datum vytvoření", auto_now_add=True)

    class Meta:
        verbose_name = "Přihláška do ročníku"
        verbose_name_plural = "Přihlášky do ročníku"

    def __str__(self):
        return f"Přihláška <{self.participant.user}> do ročníku <{self.grade}> z {self.created_at}"


class TaskSolutionSubmission(models.Model):
    application = models.ForeignKey(
        GradeApplication,
        verbose_name="Přihláška",
        null=False,
        blank=False,
        on_delete=models.CASCADE,
        related_name="solution_submissions",
    )
    task = models.ForeignKey(
        Task,
        verbose_name="Úloha",
        null=False,
        blank=False,
        on_delete=models.PROTECT,
        related_name="solution_submissions",
    )
    # If file is NULL, it means that the solution has been submitted by post
    file = models.FileField(
        verbose_name="Soubor s řešením",
        upload_to="rocniky/reseni/",
        null=True,
        blank=True,
    )
    file_for_export_normal = models.FileField(
        verbose_name="Soubor s řešením připravený pro export (bez duplexu)",
        upload_to="rocniky/reseni-pro-export/",
        null=True,
        blank=True,
    )
    file_for_export_duplex = models.FileField(
        verbose_name="Soubor s řešením připravený pro export (s duplexem)",
        upload_to="rocniky/reseni-pro-export/",
        null=True,
        blank=True,
    )
    score = models.DecimalField(
        verbose_name="Skóre", max_digits=5, decimal_places=2, null=True, blank=True
    )
    submitted_at = models.DateTimeField(verbose_name="Datum nahrání", auto_now_add=True)
    stickers = models.ManyToManyField(
        "Sticker", blank=True, related_name="solution_uses"
    )

    class Meta:
        verbose_name = "Odevzdané řešení"
        verbose_name_plural = "Odevzdaná řešení"
        permissions = (
            ("change_solution_submission_presence", "Úprava stavu odevzdání řešení"),
            ("scoring", "Bodování"),
        )

    def __str__(self):
        return f"Řešení <{self.task}> pro přihlášku <{self.application_id}>"


    def delete(self, *args, **kwargs):
        self.file.delete()
        super().delete(*args, **kwargs)

    def prepare_for_export(self):
        """Use uploaded file to prepare export-ready variants (normal and duplex)."""
        logger.info(
            "Prepare uploaded file from application %r and task for export",
            self.application.id,
            self.task.nr,
        )

        if self.file:
            file_normal, file_duplex = prepare_submission_for_export(
                in_file=self.file,
                label=f"Řešitel: {self.application.participant.get_full_name()}       Úloha č. {self.task.nr}".encode(
                    "utf8"
                ),
            )

            with tempfile.TemporaryFile() as tf:
                file_normal.write(tf)
                self.file_for_export_normal.save(
                    f"submission_{self.application.pk}_{self.task.nr}_normal.pdf",
                    File(tf),
                )

            with tempfile.TemporaryFile() as tf:
                file_duplex.write(tf)
                self.file_for_export_duplex.save(
                    f"submission_{self.application.pk}_{self.task.nr}_duplex.pdf",
                    File(tf),
                )

            logger.debug("Export versions prepared OK")
        else:
            logger.warning("Export version prepare failed - no valid file available")


class StickerManager(models.Manager):
    def get_by_natural_key(self, nr):
        return self.get(nr=nr)


class Sticker(models.Model):
    title = models.CharField(
        verbose_name="Název", max_length=255, null=False, blank=False
    )
    description = models.TextField(verbose_name="Popis", null=True, blank=True)
    nr = models.PositiveSmallIntegerField(
        verbose_name="Číslo", null=False, db_index=True, unique=True
    )
    handpicked = models.BooleanField(
        verbose_name="Přiřazován ručně", default=True, null=False, db_index=True
    )

    objects = StickerManager()

    class Meta:
        verbose_name = "Nálepka"
        verbose_name_plural = "Nálepky"
        ordering = ("nr", "title")

    def __str__(self):
        return f"{self.nr} - {self.title}"

    def natural_key(self):
        return (self.nr,)


class EventAttendee(models.Model):
    user = models.ForeignKey(User, verbose_name="Účastník", on_delete=models.CASCADE)
    event = models.ForeignKey(
        "core.Event", verbose_name="Akce", on_delete=models.CASCADE
    )
    signup_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Datum přihlášky",
        help_text="Bude využito při vyhodnocování náhradníků.",
    )

    class Meta:
        verbose_name = "Přihláška na akci"
        verbose_name_plural = "Přihlášky na akce"
        ordering = ("signup_date",)
        unique_together = ("user", "event")

    def __str__(self):
        return f"{self.user.get_full_name()} chce jet na {self.event}"


class EventQuerySet(models.QuerySet):
    def visible_to(self, user):
        if user is not None and user.is_authenticated:
            return self.filter(models.Q(is_public=True) | models.Q(visible_to=user))
        return self.filter(is_public=True)

    def future(self, current=None):
        current_date = current or date.today()
        return self.filter(end_date__gte=current_date)

    def past(self, current=None):
        current_date = current or date.today()
        return self.filter(end_date__lt=current_date)

    def accepting_enlistments(self, current=None):
        return self.filter(enlistment_enabled=True)


class Event(models.Model):
    title = models.CharField(verbose_name="Název", max_length=150, null=False)
    description = models.TextField(verbose_name="Popis", null=False, blank=True)
    place = models.CharField(verbose_name="Místo konání", max_length=150, null=True)
    start_date = models.DateField(
        verbose_name="Začíná",
        null=False,
        blank=False,
        db_index=True,
    )
    end_date = models.DateField(
        verbose_name="Končí",
        null=False,
        blank=False,
        db_index=True,
    )
    capacity = models.PositiveSmallIntegerField(
        verbose_name="Doporučený max. počet účastníků", null=True, blank=True
    )
    enlistment_message = models.TextField(
        verbose_name="Zpráva po přihlášení", null=False, blank=True
    )
    enlistment_enabled = models.BooleanField(
        verbose_name="Přihlášení je umožněno", default=False
    )
    is_public = models.BooleanField(
        verbose_name="Veřejná akce",
        help_text="Neveřejné akce se zobrazí jen níže uvedeným osobám.",
        default=True,
    )
    publish_occupancy = models.BooleanField(
        verbose_name="Zveřejnit počet účastníků",
        help_text="Pokud je zaškrtnuto, u akce se zobrazí kapacita i aktuální "
        "obsazenost.",
        default=True,
    )
    attendees = models.ManyToManyField(
        User, verbose_name="Účastníci", blank=True, through=EventAttendee
    )
    visible_to = models.ManyToManyField(
        User,
        verbose_name="Viditelné pro tyto uživatele",
        help_text="Využijte pro neveřejné akce. Pokud je akce neveřejná, bude "
        "se zobrazovat jen zde vybraným uživatelům. U veřejných akcí se "
        "nezohledňuje.",
        related_name="private_events",
        blank=True,
    )
    reward_stickers = models.ManyToManyField(
        Sticker,
        verbose_name="Nálepky pro účastníky",
        blank=True,
        help_text="Každý účastník získá zvolené nálepky. Uděleny budou v rámci "
        "série, která datumově následuje po akci.",
        related_name="event_uses",
    )

    objects = EventQuerySet.as_manager()

    class Meta:
        verbose_name = "Akce"
        verbose_name_plural = "Akce"
        ordering = ("-start_date",)
        permissions = (("export_event_attendees", "Export účastníků akce"),)

    def __str__(self):
        return str(self.title)

    def _build_url(self, name):
        return reverse(name, kwargs={"pk": self.pk, "slug": slugify(self.title)})

    def get_absolute_url(self):
        return self._build_url("core:event_detail")

    def get_enlist_url(self):
        return self._build_url("core:event_enlist")

    def get_export_url(self):
        return self._build_url("core:event_attendees_export")

    @property
    def is_accepting_enlistments(self):
        return self.enlistment_enabled and date.today() <= self.end_date


class FlatPageMeta(models.Model):
    flatpage = models.OneToOneField(
        to="flatpages.FlatPage",
        on_delete=models.CASCADE,
        verbose_name="Stránka",
        related_name="metadata",
    )
    title = models.CharField("Titulek", max_length=255, blank=True)
    keywords = models.CharField(
        "Klíčová slova", help_text="Oddělujte čárkou", max_length=150, blank=True
    )
    description = models.TextField("Krátký popis", blank=True)
    allowed_groups = models.ManyToManyField(
        UserGroup,
        verbose_name="Povoleno pro tyto skupiny",
        help_text="Pokud zde něco zvolíte, stránka bude dostupná pouze pro "
        "uvedené skupiny. Pokud chcete nechat stránku dostupnou pro řešitele, "
        "nevyplňujte zde nic.",
        blank=True,
    )

    class Meta:
        verbose_name = "Metadata statické stránky"
        verbose_name_plural = "Metadata statických stránek"

    def __str__(self):
        return "Metadata pro %s" % self.flatpage

    def is_accessible_for(self, user):
        """Decide whether user should be allowed to display this page."""
        allowed_groups = self.allowed_groups.all()

        if len(allowed_groups) > 0 and (
            not user.is_authenticated
            or (
                not user.is_superuser
                and all(g not in allowed_groups for g in user.groups.all())
            )
        ):
            return False

        return True
