from django.db.models import TextField

from cuser.admin import UserAdmin
from markdownx.widgets import AdminMarkdownxWidget

from .models import Task, User, Grade, GradeSeries

from django.contrib import admin


class GradeSeriesInline(admin.TabularInline):
    model = GradeSeries
    min_num = 4
    max_num = 4

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Grade)
class GradeAdmin(admin.ModelAdmin):
    inlines = (GradeSeriesInline,)

    formfield_overrides = {
        TextField: {"widget": AdminMarkdownxWidget},
    }


class TaskInline(admin.TabularInline):
    model = Task
    min_num = 5
    max_num = 5


@admin.register(GradeSeries)
class GradeSeriesAdmin(admin.ModelAdmin):
    list_display = ("grade", "series", "submission_deadline")
    list_filter = ("grade",)
    list_select_related = ("grade",)
    inlines = (TaskInline,)


admin.site.register(User, UserAdmin)
