from functools import wraps

from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import redirect
from django.urls import reverse_lazy

from ..models import Grade, Participant


def is_participant(
    function=None, redirect_field_name=REDIRECT_FIELD_NAME, login_url=None
):
    """Decorator for views that checks that the user is a particpant, e.g. has a participant profile."""
    actual_decorator = user_passes_test(
        lambda u: Participant.objects.filter(user=u).exists(),
        login_url=reverse_lazy("core:current_grade"),
        redirect_field_name=redirect_field_name,
    )
    if function:
        return actual_decorator(function)
    return actual_decorator


def current_grade_exists(function):
    """Decorator that checks if current grade exists."""

    @wraps(function)
    def wrap(request, *args, **kwargs):
        grade_exists = Grade.objects.get_current() is not None

        if grade_exists:
            return function(request, *args, **kwargs)
        return redirect("core:home")

    return wrap
