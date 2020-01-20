from collections import defaultdict

from django.views.generic import ListView

from .. import models


class EventListView(ListView):
    queryset = models.Event.objects.past()
    template_name = "core/event_listing.html"

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        year_list = defaultdict(list)

        for e in data["object_list"]:
            year_list[e.start_date.year].append(e)

        data["year_list"] = year_list.items()

        return data
