from django.db.models import TextField

from cuser.admin import UserAdmin
from markdownx.widgets import AdminMarkdownxWidget

from . import models

from django.contrib import admin


class GradeSeriesInline(admin.TabularInline):
    model = models.GradeSeries
    min_num = 4
    max_num = 4

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(models.Grade)
class GradeAdmin(admin.ModelAdmin):
    inlines = (GradeSeriesInline,)

    formfield_overrides = {
        TextField: {"widget": AdminMarkdownxWidget},
    }


class TaskInline(admin.TabularInline):
    model = models.Task
    min_num = 5
    max_num = 5


@admin.register(models.GradeSeries)
class GradeSeriesAdmin(admin.ModelAdmin):
    list_display = ("grade", "series", "submission_deadline")
    list_filter = ("grade",)
    list_select_related = ("grade",)
    inlines = (TaskInline,)


@admin.register(models.Participant)
class ParticipantAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "school",
    )
    list_select_related = ("user",)


@admin.register(models.Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ("__str__", "series", "school_year")
    search_fields = ("title", "nr", "series__grade__school_year")
    list_select_related = ("series__grade",)

    def school_year(self, obj):
        return obj.series.grade.school_year

    school_year.short_description = "Školní rok"


@admin.register(models.GradeApplication)
class GradeApplicationAdmin(admin.ModelAdmin):
    search_fields = ("grade__school_year", "participant__user__email")
    list_select_related = (
        "grade",
        "participant__user",
    )


@admin.register(models.TaskSolutionSubmission)
class SolutionSubmissionAdmin(admin.ModelAdmin):
    list_display = (
        "task",
        "user",
        "series",
    )
    list_select_related = (
        "application__participant__user",
        "task__series",
    )
    autocomplete_fields = ("task", "application")

    def user(self, obj):
        return obj.application.participant.user

    user.short_description = "Uživatel"

    def series(self, obj):
        return obj.task.series

    series.short_description = "Série"


admin.site.register(models.User, UserAdmin)
