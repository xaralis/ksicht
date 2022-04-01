from re import search
from cuser.admin import UserAdmin
from django import forms
from django.contrib import admin
from django.contrib.auth.models import Permission
from django.contrib.flatpages.admin import FlatPageAdmin
from django.contrib.flatpages.models import FlatPage
from django.db.models import TextField
from django.forms.models import BaseInlineFormSet
from markdownx.widgets import AdminMarkdownxWidget

from . import models


class GradeSeriesInlineFormSet(BaseInlineFormSet):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.initial = [
            {"series": "1"},
            {"series": "2"},
            {"series": "3"},
            {"series": "4"},
        ]


class GradeSeriesInline(admin.TabularInline):
    model = models.GradeSeries
    min_num = 4
    max_num = 4
    formset = GradeSeriesInlineFormSet

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(models.Grade)
class GradeAdmin(admin.ModelAdmin):
    inlines = (GradeSeriesInline,)

    formfield_overrides = {
        TextField: {"widget": AdminMarkdownxWidget},
    }


class TaskInlineFormSet(BaseInlineFormSet):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.initial = [
            {"nr": "1"},
            {"nr": "2"},
            {"nr": "3"},
            {"nr": "4"},
            {"nr": "5"},
        ]


class TaskInline(admin.TabularInline):
    model = models.Task
    min_num = 5
    max_num = 5
    formset = TaskInlineFormSet


class GradeSeriesAttachmentInline(admin.TabularInline):
    model = models.GradeSeriesAttachment
    extra = 0


@admin.register(models.GradeSeries)
class GradeSeriesAdmin(admin.ModelAdmin):
    list_display = ("grade", "series", "submission_deadline")
    list_filter = ("grade",)
    list_select_related = ("grade",)
    inlines = (GradeSeriesAttachmentInline, TaskInline)
    ordering = ("grade", "-submission_deadline")


@admin.register(models.Participant)
class ParticipantAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "first_name",
        "last_name",
        "school",
    )
    list_select_related = ("user",)
    readonly_fields = ("first_name", "last_name")
    actions = ['increase_school_year']

    def first_name(self, obj):
        return obj.user.first_name

    def last_name(self, obj):
        return obj.user.last_name

    def increase_school_year(self, request, queryset):
        for participant in queryset:
            
            #index = participant.GRADE_CHOICES.index(participant.school_year)
            #participant.school_year = participant.GRADE_CHOICES[index - 1]
            GCH0, GCH1 = zip(*participant.GRADE_CHOICES)
            print(GCH0, flush=True)
            index = GCH0.index(participant.school_year)
            print(index, flush=True)
            print(participant.GRADE_CHOICES[index - 1], flush=True)
            if index != 0:
                participant.school_year = participant.GRADE_CHOICES[index - 1][0]
                participant.save()

    increase_school_year.short_description = 'Zvýšit ročník studia'


@admin.register(models.Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ("nr", "title", "series", "school_year")
    search_fields = ("title", "nr", "series__grade__school_year")
    list_select_related = ("series__grade",)
    list_filter = ("series__grade",)

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
    actions = ['paste_school_grade']

    def paste_school_grade(self, request, queryset):
        for application in queryset:
            application.participant_current_grade = application.participant.school_year
            application.save()

    paste_school_grade.short_description = 'Změnit ročník studia v přihlášce.'
    


@admin.register(models.TaskSolutionSubmission)
class SolutionSubmissionAdmin(admin.ModelAdmin):
    
    list_display = (
        "task",
        "user",
        "series",
        "score",
        "submitted_at",
    )
    list_select_related = (
        "application__participant__user",
        "task__series",
    )
    autocomplete_fields = ("task", "application")
    readonly_fields = ("submitted_at",)
    ordering = ("application__participant__user__last_name",)
    search_fields = ("application__participant__user__last_name", "application__participant__user__first_name")

    def user(self, obj):
        return obj.application.participant.user

    user.short_description = "Uživatel"

    def series(self, obj):
        return obj.task.series

    series.short_description = "Série"


@admin.register(models.Sticker)
class StickerAdmin(admin.ModelAdmin):
    search_fields = ("nr", "title")
    list_display = ("nr", "title", "handpicked")


class EventAttendeeInline(admin.TabularInline):
    model = models.EventAttendee
    readonly_fields = ("signup_date",)


class EventAdminForm(forms.ModelForm):
    class Meta:
        model = models.Event
        fields = "__all__"  # required in new versions

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["visible_to"].queryset = self.fields[
            "visible_to"
        ].queryset.order_by("last_name", "first_name", "email")


@admin.register(models.Event)
class EventAdmin(admin.ModelAdmin):
    search_fields = ("title",)
    list_display = (
        "title",
        "place",
        "start_date",
        "end_date",
        "capacity",
        "enlistment_enabled",
        "is_public",
        "publish_occupancy",
    )
    list_filter = ("is_public", "enlistment_enabled")
    inlines = (EventAttendeeInline,)
    date_hierarchy = "start_date"

    formfield_overrides = {
        TextField: {"widget": AdminMarkdownxWidget},
    }

    form = EventAdminForm


admin.site.register(Permission)
admin.site.register(models.User, UserAdmin)


class MetadataInline(admin.StackedInline):
    model = models.FlatPageMeta


class MarkdownFlatPageAdmin(FlatPageAdmin):
    inlines = (MetadataInline,)
    formfield_overrides = {
        TextField: {"widget": AdminMarkdownxWidget},
    }


admin.site.unregister(FlatPage)
admin.site.register(FlatPage, MarkdownFlatPageAdmin)
