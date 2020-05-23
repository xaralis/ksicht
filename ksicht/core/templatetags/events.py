from datetime import date

from django import template

from ksicht.core.models import Event


register = template.Library()


@register.simple_tag(takes_context=True)
def event_list(context, list_type):
    queryset = Event.objects.all().prefetch_related("attendees")
    today = date.today()
    results = []

    if list_type == "future":
        queryset = queryset.filter(start_date__gte=today)
    elif list_type == "past":
        queryset = queryset.filter(end_date__lt=today)

    for e in queryset:
        enlisted = context["request"].user in e.attendees.all()
        can_enlist = (
            e.is_accepting_enlistments
            and context["request"].user.is_authenticated
            and not enlisted
        )
        results.append((e, enlisted, can_enlist))

    return results
