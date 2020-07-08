from urllib.parse import quote

from django.conf import settings
from django.http import HttpResponse
from django.views.generic import View
from django.views.generic.detail import BaseDetailView

from ksicht import pdf
from .. import models
from ..constants import SCHOOLS


__all__ = (
    "SeriesTaskEnvelopesPrintout",
    "ActiveParticipantsEnvelopesPrintout",
    "AllParticipantsEnvelopesPrintout",
)


class SeriesTaskEnvelopesPrintout(View):
    def get(self, request, *args, **kwargs):
        response = HttpResponse(content_type="application/pdf")
        response["Content-Disposition"] = "attachment; filename*=UTF-8''{}.pdf".format(
            quote("Obálky pro školy")
        )

        def _build_lines(s):
            # If street exists
            if s[9]:
                return (
                    "K rukám učitelů chemie",
                    s[6],
                    s[8],
                    f"{s[13]} {s[14]}",
                )
            return ("K rukám učitelů chemie", s[6], s[14], s[13])

        lines = [_build_lines(s) for s in SCHOOLS]

        pdf.envelopes(lines, settings.KSICHT_CONTACT_ADDRESS_LINES, response)

        return response


class ParticipantEnvelopesPrintout:
    def render_to_response(self, context):
        participants = self.get_participants(context)
        title = self.get_title(context)

        response = HttpResponse(content_type="application/pdf")
        response["Content-Disposition"] = "attachment; filename*=UTF-8''{}.pdf".format(
            quote(title)
        )

        lines = [
            (
                p.get_full_name(),
                p.street,
                f"{p.zip_code} {p.city}",
                p.get_country_display(),
            )
            for p in participants
        ]

        pdf.envelopes(lines, settings.KSICHT_CONTACT_ADDRESS_LINES, response)

        return response

    def get_participants(self, context):
        raise NotImplementedError()

    def get_title(self, context):
        raise NotImplementedError()


class ActiveParticipantsEnvelopesPrintout(BaseDetailView, ParticipantEnvelopesPrintout):
    queryset = models.GradeSeries.objects.all()

    def get_participants(self, context):
        series = context["object"]
        active_participants = models.Participant.objects.active_in_series(
            series
        ).order_by("user__last_name", "user__first_name", "user__email")

        return active_participants

    def get_title(self, context):
        return str(context["object"]) + " - obálky pro řešitele"


class AllParticipantsEnvelopesPrintout(BaseDetailView, ParticipantEnvelopesPrintout):
    queryset = models.Grade.objects.all()

    def get_participants(self, context):
        grade = context["object"]
        active_participants = models.Participant.objects.filter(
            applications=grade
        ).order_by("user__last_name", "user__first_name", "user__email")

        return active_participants

    def get_title(self, context):
        return "Ročník " + str(context["object"]) + " - obálky pro přihlášené"

