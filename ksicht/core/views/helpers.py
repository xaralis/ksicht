from ..models import Grade


def get_current_grade_context(user):
    context = {}
    context["current_grade"] = current_grade = Grade.objects.get_current()
    context["current_series"] = (
        current_grade.get_current_series() if current_grade else None
    )
    context["is_current_grade_participant"] = (
        current_grade.participants.filter(user=user).exists()
        if current_grade
        else False
    )
    return context


class CurrentGradeMixin:
    def dispatch(self, *args, **kwargs):
        self.grade_context = get_current_grade_context(self.request.user)
        return super().dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(self.grade_context)
        return context
