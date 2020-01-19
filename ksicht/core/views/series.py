from django.views.generic.detail import DetailView

from .. import models


__all__ = (
    "SeriesResultsView",
)


class SeriesResultsView(DetailView):
    template_name = "core/series_results.html"
    queryset = models.GradeSeries.objects.filter(results_published=True).select_related("grade").prefetch_related("tasks")
