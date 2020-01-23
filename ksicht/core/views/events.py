from collections import defaultdict

from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import Http404
from django.utils.decorators import method_decorator
from django.views.generic import DetailView, ListView

from .. import models


def is_enlisted(user, event):
    return user.is_authenticated and user in event.attendees.all()


class EventListView(ListView):
    queryset = models.Event.objects.all().prefetch_related("attendees")
    template_name = "core/event_listing.html"

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        year_list = defaultdict(list)

        for e in data["object_list"]:
            enlisted = self.request.user in e.attendees.all()
            can_enlist = (
                e.is_accepting_enlistments
                and self.request.user.is_authenticated
                and not enlisted
            )
            year_list[e.start_date.year].append((e, enlisted, can_enlist))

        data["year_list"] = year_list.items()

        return data


class EventDetailView(DetailView):
    queryset = models.Event.objects.all().prefetch_related("attendees")
    template_name = "core/event_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["is_enlisted"] = is_enlisted(self.request.user, self.object)
        context["can_enlist"] = (
            self.object.is_accepting_enlistments
            and self.request.user.is_authenticated
            and not context["is_enlisted"]
        )
        context["attendee_count"] = self.object.attendees.count()
        context["free_places"] = max(
            0, self.object.capacity - context["attendee_count"]
        )
        return context


@method_decorator([login_required], name="dispatch")
class EventEnlistView(DetailView):
    queryset = models.Event.objects.accepting_enlistments().prefetch_related(
        "attendees"
    )
    template_name = "core/event_enlist.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["attendee_count"] = self.object.attendees.count()
        context["free_places"] = max(
            0, self.object.capacity - context["attendee_count"]
        )

        # Make sure user can still enlist.
        can_enlist = not is_enlisted(self.request.user, self.object)

        if not can_enlist:
            raise Http404()

        return context

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(object=self.object)

        attendee = self.object.attendees.add(self.request.user)

        context["has_enlisted"] = True
        context["is_substitue"] = self.object.capacity > context["attendee_count"]

        return self.render_to_response(context)
