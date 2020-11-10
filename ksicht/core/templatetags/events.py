from django import template

from ksicht.core.models import Event


register = template.Library()


@register.simple_tag(takes_context=True)
def event_list(context, list_type):
    queryset = Event.objects.all().prefetch_related("attendees")
    results = []

    if list_type == "future":
        queryset = queryset.visible_to(context["request"].user).future()
    elif list_type == "past":
        queryset = queryset.visible_to(context["request"].user).past()

    for e in queryset:
        enlisted = context["request"].user in e.attendees.all()
        can_enlist = (
            e.is_accepting_enlistments
            and context["request"].user.is_authenticated
            and not enlisted
        )
        results.append((e, enlisted, can_enlist))

    return results
