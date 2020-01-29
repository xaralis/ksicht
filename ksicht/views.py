from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from django.views.generic import UpdateView
import pydash as py_

from . import forms


class UserProfileEditView(UpdateView):
    form_class = forms.KsichtEditProfileForm
    template_name = "registration/user_change_form.html"
    success_url = reverse_lazy("core:home")

    @method_decorator(csrf_protect)
    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get_object(self, queryset=None):
        return self.request.user

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()

        if hasattr(self, "object"):
            kwargs.update(
                {
                    "initial": py_.pick(
                        self.object.participant_profile, self.form_class.PROFILE_FIELDS
                    )
                }
            )
        return kwargs

    def form_valid(self, form):
        messages.add_message(
            self.request,
            messages.SUCCESS,
            f"<i class='fas fa-check-circle notification-icon'></i> Váš profil byl aktualizován</strong>.",
        )
        return super().form_valid(form)
