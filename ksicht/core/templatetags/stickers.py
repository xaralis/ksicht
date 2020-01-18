from django import template


register = template.Library()


@register.inclusion_tag("core/includes/sticker.html")
def sticker(sticker):
    return {"nr": sticker.nr, "title": sticker.title}
