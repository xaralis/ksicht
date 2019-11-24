from django.urls import path
from django.views.generic import DetailView

from . import views, models


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
        "rocniky/<grade_id>/odevzdane-ulohy/",
        views.SubmissionOverview.as_view(),
        name="submission_overview",
    ),
    path(
        "rocniky/<grade_id>/serie/<pk>/",
        DetailView.as_view(template_name="core/manage/series_detail.html", queryset=models.GradeSeries.objects.all()),
        name="series_detail",
    ),
    path(
        "rocniky/<grade_id>/bodovani/<task_id>/",
        views.ScoringView.as_view(),
        name="scoring",
    ),
]
