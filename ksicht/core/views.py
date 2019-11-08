from django.views.generic import TemplateView


class HomeView(TemplateView):
    def get_template_names(self):
        if self.request.user.is_authenticated:
            return ["core/dashboard.html"]
        return "core/home.html"
