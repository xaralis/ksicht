from django.views.generic import TemplateView

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
