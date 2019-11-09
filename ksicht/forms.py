from django import forms
from django.core import validators

import pydash as py_
from cuser.forms import UserCreationForm, AuthenticationForm
from crispy_forms.helper import FormHelper
from django_registration import validators as reg_validators
from webpack_loader.templatetags.webpack_loader import webpack_static

from ksicht.core import constants
from ksicht.core.models import User, Participant
from ksicht.bulma.layout import Row, Column, Layout, Submit

from django.contrib.auth.forms import SetPasswordForm, PasswordResetForm

zip_validator = validators.RegexValidator(
    r"^\d{3} ?\d{2}$", "Zadejte PSČ ve formátu 123 45."
)
phone_validator = validators.RegexValidator(
    r"^(\+420)? ?[1-9][0-9]{2} ?[0-9]{3} ?[0-9]{3}$",
    "Zadejte telefon ve formátu +420 777 123123.",
)


class KsichtRegistrationForm(UserCreationForm):
    phone = forms.CharField(
        label="Telefon",
        max_length=20,
        required=False,
        initial="+420",
        help_text="Telefon ve formátu +420 777 123123.",
    )
    street = forms.CharField(label="Ulice", max_length=100)
    city = forms.CharField(label="Obec", max_length=100)
    zip_code = forms.CharField(
        label="PSČ", max_length=10, required=True, validators=[zip_validator]
    )
    country = forms.ChoiceField(label="Stát", choices=Participant.COUNTRY_CHOICES)
    school = forms.ChoiceField(
        label="Škola",
        choices=constants.SCHOOLS,
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

    class Meta:
        model = User
        fields = ("email",)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        email_field = User.get_email_field_name()
        self.fields[email_field].validators.append(
            reg_validators.CaseInsensitiveUnique(
                User, email_field, reg_validators.DUPLICATE_EMAIL
            )
        )

        self.fields["tos"] = forms.BooleanField(
            widget=forms.CheckboxInput,
            label=f"Přečetl/a jsem si a souhlasím s <a href='{webpack_static('attachments/zpracovani-osobnich-udaju-pro-web.pdf')}' target='_blank' rel='noopener'>podmínkami použití a zpracováním osobních údajů</a>",
        )

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(Column("email"), Column("phone")),
            Row(Column("password1"), Column("password2")),
            Row(Column("street", css_class="is-10"),),
            Row(
                Column("zip_code", css_class="is-2"),
                Column("city", css_class="is-4"),
                Column("country", css_class="is-2 is-offset-2"),
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

        # Run validation
        phone_validator(phone)

        return phone

    def clean_school(self):
        cd = self.cleaned_data
        school = cd.get("school")

        if school == "--jiná--":
            if not all(
                (
                    cd.get("school_alt_name"),
                    cd.get("school_alt_street"),
                    cd.get("school_alt_zip_code"),
                    cd.get("school_alt_city"),
                )
            ):
                raise validators.ValidationError(
                    "Vyberte konkrétní školu, nebo vyplňte dodatečné informace níže."
                )

        return school

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
            Row(Column("email")),
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
