from django.views.generic import TemplateView
from django.views.generic.detail import DetailView

from .models import Grade


class HomeView(TemplateView):
    def get_template_names(self):
        if self.request.user.is_authenticated:
            return ["core/dashboard.html"]
        return "core/home.html"


class CurrentGradeView(DetailView):
    template_name = "core/current_grade.html"

    def get_object(self, *args, **kwargs):
        return Grade.objects.get_current()
