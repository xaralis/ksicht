from django.conf import settings
from django.views.generic.base import TemplateView


__all__ = ("PeopleView",)


class PeopleView(TemplateView):
    template_name = "core/people.html"

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data["people"] = settings.KSICHT_PEOPLE
        return data
