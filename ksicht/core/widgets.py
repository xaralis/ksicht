from django import forms
from django.utils.html import escape
from django.utils.safestring import mark_safe


class RendererWidget(forms.Widget):
    def render(self, name, value, attrs=None, renderer=None):
        return mark_safe(value)


class CurrentChoiceRendererWidget(forms.Widget):
    def render(self, name, value, attrs=None, renderer=None):
        for key, val in self.choices:
            if key == value or key == int(value):
                return escape(val) + mark_safe(
                    f"<input type='hidden' name='{name}' value='{value}'>"
                )

        return escape(value) + mark_safe(
            f"<input type='hidden' name='{name}' value='{value}'>"
        )
