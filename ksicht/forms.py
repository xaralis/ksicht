from django import forms
from django.core import validators
from django.contrib.auth.forms import (
    AuthenticationForm,
    PasswordResetForm,
    SetPasswordForm,
)

from django_registration import forms as reg_forms
from crispy_forms.helper import FormHelper
import pydash as py_

from ksicht.core.models import Participant
from ksicht.bulma.layout import Submit, Column, Row, Layout


zip_validator = validators.RegexValidator(
    r"^\d{3} ?\d{2}$", "Zadejte PSČ ve formátu 123 45."
)
phone_validator = validators.RegexValidator(
    r"^(\+420)? ?[1-9][0-9]{2} ?[0-9]{3} ?[0-9]{3}$",
    "Zadejte telefon ve formátu +420 777 123123.",
)


class KsichtRegistrationForm(
    reg_forms.RegistrationFormCaseInsensitive,
    reg_forms.RegistrationFormTermsOfService,
    reg_forms.RegistrationFormUniqueEmail,
):
    phone = forms.CharField(
        label="Telefon", max_length=20, required=False, validators=[phone_validator]
    )
    street = forms.CharField(label="Ulice", max_length=100)
    city = forms.CharField(label="Obec", max_length=100)
    zip_code = forms.CharField(
        label="PSČ", max_length=10, required=True, validators=[zip_validator]
    )
    country = forms.ChoiceField(label="Stát", choices=Participant.COUNTRY_CHOICES)
    school = forms.CharField(
        label="Škola",
        max_length=80,
        required=True,
        help_text="Vyberte školu z nabídky. Pokud vaše škola chybí, vyplňte prosím informace níže.",
    )
    school_year = forms.ChoiceField(
        label="Ročník", required=True, choices=Participant.GRADE_CHOICES
    )
    school_alt_name = forms.CharField(
        label="Název školy", max_length=80, required=False
    )
    school_alt_street = forms.CharField(
        label="Ulice školy", max_length=100, required=False
    )
    school_alt_city = forms.CharField(
        label="Obec školy", max_length=100, required=False
    )
    school_alt_zip_code = forms.CharField(
        label="PSČ školy", max_length=10, required=False, validators=[zip_validator]
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(Column("username"), Column("email"), Column("phone")),
            Row(Column("password1"), Column("password2")),
            Row(
                Column("street"), Column("zip_code"), Column("city"), Column("country")
            ),
            Row(Column("school"), Column("school_year")),
            Row(
                Column("school_alt_name"),
                Column("school_alt_street"),
                Column("school_alt_zip_code"),
                Column("school_alt_city"),
            ),
            Row(Column("tos")),
            Submit("submit", "Pokračovat"),
        )

    def clean_phone(self):
        phone = self.cleaned_data.get("phone")
        if phone == "+420":
            return None
        return phone

    def save(self, commit=True):
        user = super().save(commit)
        cd = self.cleaned_data

        user.is_active = False
        user.save()

        user.participant = Participant(
            **py_.pick(
                cd,
                "phone",
                "street",
                "city",
                "zip_code",
                "country",
                "school",
                "school_year",
                "school_alt_name",
                "schole_alt_street",
                "school_alt_city",
                "school_alt_zip_code",
            )
        )
        user.participant.save()

        return user


class KsichtAuthenticationForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(Column("username")),
            Row(Column("password")),
            Submit("submit", "Přihlásit se"),
        )


class KsichtPasswordResetForm(PasswordResetForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(Column("email")), Submit("submit", "Pokračovat"),
        )


class KsichtSetPasswordForm(SetPasswordForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(Column("new_password1")),
            Row(Column("new_password2")),
            Submit("submit", "Nastavit nové heslo"),
        )
