from django import template

from ksicht.core.models import Grade


register = template.Library()


@register.simple_tag
def grade_list(count=5):
    return Grade.objects.all()[:count]
