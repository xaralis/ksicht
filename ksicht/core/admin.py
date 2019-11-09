from django.contrib import admin
from django.contrib.admin.widgets import AdminDateWidget
from django.contrib.postgres.forms.ranges import RangeWidget
from django.contrib.postgres.fields import DateRangeField
from django.db.models import TextField

from cuser.admin import UserAdmin
from markdownx.widgets import AdminMarkdownxWidget

from .models import User, Grade, GradeSeries


class GradeSeriesInline(admin.TabularInline):
    model = GradeSeries
    min_num = 4
    max_num = 4

    def has_delete_permission(self, request, obj=None):
        return False


class GradeAdmin(admin.ModelAdmin):
    inlines = (GradeSeriesInline,)
    # form = GradeForm

    formfield_overrides = {
        TextField: {'widget': AdminMarkdownxWidget},
        DateRangeField: {'widget': RangeWidget(AdminDateWidget())}
    }


admin.site.register(User, UserAdmin)
admin.site.register(Grade, GradeAdmin)
