from django.db.models import Count
from django.views.generic.detail import DetailView

from .. import models


__all__ = (
    "SeriesDetailView",
    "SeriesResultsView",
)


class SeriesDetailView(DetailView):
    queryset = models.GradeSeries.objects.all()
    template_name = "core/manage/series_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["tasks"] = self.object.tasks.all().annotate(submission_count=Count("solution_submissions"))
        return context

class SeriesResultsView(DetailView):
    template_name = "core/series_results.html"
    queryset = (
        models.GradeSeries.objects.filter(results_published=True)
        .select_related("grade")
        .prefetch_related("tasks")
    )


