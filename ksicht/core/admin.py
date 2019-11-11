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


admin.site.register(models.User, UserAdmin)
