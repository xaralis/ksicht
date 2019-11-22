from django.views.generic import TemplateView

from ..models import Grade
from .helpers import CurrentGradeMixin


__all__ = ("HomeView",)


class HomeView(CurrentGradeMixin, TemplateView):
    @property
    def is_dashboard(self):
        return self.request.user.is_authenticated

    def get_template_names(self):
        if self.is_dashboard:
            return ["core/dashboard.html"]
        return "core/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if self.is_dashboard:
            context["grades"] = Grade.objects.all()[:5]

        return context
