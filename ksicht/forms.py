from crispy_forms.helper import FormHelper
from cuser.forms import AuthenticationForm, UserChangeForm, UserCreationForm
from django import forms
from django.contrib.auth.forms import PasswordChangeForm, PasswordResetForm, SetPasswordForm
from django.core import validators
from django_registration import validators as reg_validators
import pydash as py_
from webpack_loader.templatetags.webpack_loader import webpack_static

from ksicht.bulma.layout import Field, Column, FormActions, FormControl, Layout, Link, Row, Submit
from ksicht.core import constants
from ksicht.core.models import Grade, Participant, User


zip_validator = validators.RegexValidator(
    r"^\d{3} ?\d{2}$", "Zadejte PSČ ve formátu 123 45."
)
phone_validator = validators.RegexValidator(
    r"^\+?[0-9 ]{9,}$", "Zadejte platný telefon ve formátu +420 777 123123.",
)


class KsichtProfileMixin(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["phone"] = forms.CharField(
            label="Telefon",
            max_length=20,
            required=False,
            initial="+420",
            help_text="Telefon ve formátu +420 777 123123.",
        )
        self.fields["street"] = forms.CharField(label="Ulice", max_length=100)
        self.fields["city"] = forms.CharField(label="Obec", max_length=100)
        self.fields["zip_code"] = forms.CharField(
            label="PSČ", max_length=10, required=True, validators=[zip_validator]
        )
        self.fields["country"] = forms.ChoiceField(
            label="Stát", choices=Participant.COUNTRY_CHOICES
        )
        self.fields["school"] = forms.ChoiceField(
            label="Škola",
            choices=constants.SCHOOLS_CHOICES,
            required=True,
            help_text="Vyberte školu z nabídky. Pokud vaše škola chybí, vyplňte prosím informace níže.",
        )
        self.fields["school_year"] = forms.ChoiceField(
            label="Ročník", required=True, choices=Participant.GRADE_CHOICES
        )
        self.fields["school_alt_name"] = forms.CharField(
            label="Název školy", max_length=80, required=False
        )
        self.fields["school_alt_street"] = forms.CharField(
            label="Ulice školy", max_length=100, required=False
        )
        self.fields["school_alt_city"] = forms.CharField(
            label="Obec školy", max_length=100, required=False
        )
        self.fields["school_alt_zip_code"] = forms.CharField(
            label="PSČ školy", max_length=10, required=False, validators=[zip_validator]
        )

        self.fields["first_name"].required = True
        self.fields["first_name"].widget.attrs["autofocus"] = True
        self.fields["last_name"].required = True
        self.fields["email"].widget.attrs["autofocus"] = False

    def clean_phone(self):
        phone = self.cleaned_data.get("phone")

        if phone == "+420":
            return None

        # Run validation
        phone_validator(phone)

        return phone

    def clean(self):
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
                self.add_error(
                    "school",
                    validators.ValidationError(
                        "Vyberte konkrétní školu, nebo vyplňte dodatečné informace níže."
                    ),
                )

        return cd


class KsichtRegistrationForm(KsichtProfileMixin, UserCreationForm):
    class Meta:
        model = User
        fields = ("email", "first_name", "last_name")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        email_field = User.get_email_field_name()
        self.fields[email_field].validators.append(
            reg_validators.CaseInsensitiveUnique(
                User, email_field, reg_validators.DUPLICATE_EMAIL
            )
        )
        self.fields[email_field].label = "Emailová adresa"
        self.fields[email_field].help_text = "Slouží jako uživatelské jméno pro přihlášení."

        self.fields["tos"] = forms.BooleanField(
            widget=forms.CheckboxInput,
            label=f"Přečetl/a jsem si a souhlasím s <a href='{webpack_static('attachments/zpracovani-osobnich-udaju-pro-web.pdf')}' target='_blank' rel='noopener'>podmínkami použití a zpracováním osobních údajů</a>",
        )

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(Column(Field("email", autocomplete="email"))),
            Row(Column("password1"), Column("password2")),
            Row(Column("first_name"), Column("last_name"), Column(Field("phone", autocomplete="phone"))),
            Row(Column("street")),
            Row(
                Column("zip_code", css_class="is-2"),
                Column("city", css_class="is-4"),
                Column("country", css_class="is-4 is-offset-2"),
            ),
            Row(Column("school"), Column("school_year")),
            Row(
                Column("school_alt_name"),
                Column("school_alt_street"),
                Column("school_alt_zip_code"),
                Column("school_alt_city"),
            ),
            Row(Column("tos")),
            FormActions(
                FormControl(Submit("submit", "Pokračovat")),
                FormControl(Link("core:home", "Zpět", "button is-text")),
            ),
        )

    def save(self, commit=True):
        user = super().save(commit)
        cd = self.cleaned_data
        current_grade = Grade.objects.get_current()

        user.is_active = False
        user.save()

        user.participant_profile = Participant(
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
        user.participant_profile.save()

        if current_grade:
            user.participant_profile.applications.add(current_grade)

        return user


class KsichtEditProfileForm(UserChangeForm, KsichtProfileMixin):
    PROFILE_FIELDS = (
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

    class Meta:
        model = User
        fields = ("email", "first_name", "last_name")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["email"].disabled = True

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(Column(Field("email", autocomplete="email"))),
            Row(Column("password1"), Column("password2")),
            Row(Column("first_name"), Column("last_name"), Column(Field("phone", autocomplete="phone"))),
            Row(Column("street")),
            Row(
                Column("zip_code", css_class="is-2"),
                Column("city", css_class="is-4"),
                Column("country", css_class="is-4 is-offset-2"),
            ),
            Row(Column("school"), Column("school_year")),
            Row(
                Column("school_alt_name"),
                Column("school_alt_street"),
                Column("school_alt_zip_code"),
                Column("school_alt_city"),
            ),
            FormActions(
                FormControl(Submit("submit", "Uložit změny")),
                FormControl(Link("core:home", "Zpět", "button is-text")),
            ),
        )

    def save(self, commit=True):
        user = super().save(commit)
        cd = self.cleaned_data

        user.save()

        for field, value in py_.pick(cd, *self.PROFILE_FIELDS).items():
            setattr(user.participant_profile, field, value)

        user.participant_profile.save()

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
            Row(Column("email")),
            FormActions(
                FormControl(Submit("submit", "Pokračovat")),
                FormControl(Link("core:home", "Zpět", "button is-text")),
            ),
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


class KsichtChangePasswordForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(Column("old_password")),
            Row(Column("new_password1")),
            Row(Column("new_password2")),
            FormActions(
                FormControl(Submit("submit", "Nastavit nové heslo"),),
                FormControl(Link("core:home", "Zpět", "button is-text")),
            ),
        )
