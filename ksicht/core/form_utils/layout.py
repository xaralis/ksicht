from crispy_forms.layout import (
    BaseInput,
    Div,
    HTML,
)
from django.urls import reverse


__all__ = [
    "Column",
    "Link",
    "Row",
    "Submit",
    "FormControl",
    "FormActions",
]


class Submit(BaseInput):
    """
    Used to create a Submit button descriptor for the {% crispy %} template tag.
    >>> submit = Submit("Search the Site", "search this site")

    The first argument is also slugified and turned into the id for the submit button.
    """

    field_classes = "button is-primary"
    input_type = "submit"


class Link(HTML):
    def __init__(self, urlconf, title, css_class=None):
        self.html = (
            f'<a href="{reverse(urlconf)}" class="{css_class or ""}">{title}</a>'
        )


class Row(Div):
    """
    Layout object. It wraps fields in a div whose default class is "columns".
    >>> Row("form_field_1", "form_field_2", "form_field_3")
    """

    css_class = "columns"


class Column(Div):
    """
    Layout object. It wraps fields in a div whose default class is "column".

    >>> Column("form_field_1", "form_field_2")
    """

    css_class = "column"


class FormControl(Div):
    css_class = "control"


class FormActions(Div):
    css_class = "field is-grouped"
