from django import template
from django.contrib.flatpages.models import FlatPage
from django.core.cache import cache


register = template.Library()


@register.simple_tag(takes_context=True)
def pages_by_prefix(context, prefix):
    matching_pages = cache.get(f"pages_by_prefix::{prefix}")

    if not matching_pages:
        matching_pages = FlatPage.objects.filter(
            url__startswith=prefix
        ).prefetch_related("metadata__allowed_groups")
        cache.set(f"pages_by_prefix::{prefix}", matching_pages, 120)

    return [
        p
        for p in matching_pages
        if not hasattr(p, "metadata") or p.metadata.is_accessible_for(context["user"])
    ]
