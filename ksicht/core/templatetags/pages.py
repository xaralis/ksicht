from django import template
from django.contrib.flatpages.models import FlatPage


register = template.Library()


@register.simple_tag(takes_context=True)
def pages_by_prefix(context, prefix):
    matching_pages = FlatPage.objects.filter(url__startswith=prefix).prefetch_related(
        "metadata__allowed_groups"
    )
    return [
        p
        for p in matching_pages
        if not p.metadata or p.metadata.is_accessible_for(context["user"])
    ]
