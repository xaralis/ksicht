from django.contrib.auth.decorators import permission_required
from django.urls import path
from django.utils.decorators import method_decorator
from django.views.generic import DetailView

from . import models, views


app_name = "core"


urlpatterns = [
    path("", views.HomeView.as_view(), name="home"),
    path("aktualni-rocnik/", views.CurrentGradeView.as_view(), name="current_grade"),
    path(
        "aktualni-rocnik/prihlasit-se/",
        views.CurrentGradeApplicationView.as_view(),
        name="current_grade_application",
    ),
    path(
        "aktualni-rocnik/odevzdat-reseni/",
        views.SolutionSubmitView.as_view(),
        name="solution_submit",
    ),
    path(
        "rocniky/<pk>/",
        method_decorator([permission_required("grade_view")], name="dispatch")(
            DetailView
        ).as_view(
            template_name="core/manage/grade_detail.html",
            queryset=models.Grade.objects.all(),
        ),
        name="grade_detail",
    ),
    path(
        "rocniky/<pk>/automaticke-nalepky/",
        views.AutoAssignStickersView.as_view(),
        name="grade_auto_assign_stickers",
    ),
    path(
        "rocniky/<pk>/prehled-nalepek/",
        views.StickerAssignmentOverview.as_view(),
        name="grade_sticker_assignment_overview",
    ),
    path(
        "rocniky/<grade_id>/serie/<pk>/",
        method_decorator([permission_required("gradeseries_view")], name="dispatch")(
            DetailView
        ).as_view(
            template_name="core/manage/series_detail.html",
            queryset=models.GradeSeries.objects.all(),
        ),
        name="series_detail",
    ),
    path(
        "rocniky/<grade_id>/serie/<series_id>/odevzdana-reseni/",
        views.SubmissionOverview.as_view(),
        name="submission_overview",
    ),
    path(
        "rocniky/<grade_id>/bodovani/<task_id>/",
        views.ScoringView.as_view(),
        name="task_scoring",
    ),
    path(
        "rocniky/<grade_id>/export/<task_id>/",
        views.SolutionExportView.as_view(),
        name="task_solution_export",
    ),
]
