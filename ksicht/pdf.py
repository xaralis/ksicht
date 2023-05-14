import io
from copy import deepcopy

from django.conf import settings
from pypdf import PdfReader as PdfFileReader, PdfWriter as PdfFileWriter
from pypdf.errors import PdfReadError
from pdfrw import PdfReader, PdfWriter
import reportlab
from reportlab.lib.pagesizes import A4, C3, landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph


__all__ = (
    "envelopes",
    "concatenate",
    "PdfReadError",
)

reportlab.rl_config.TTFSearchPath.append(str(settings.BASE_DIR) + "/fonts")
pdfmetrics.registerFont(TTFont("Helvetica", "Helvetica.ttf"))


def envelopes(recipient_lines, our_lines, out_file):
    """Generate envelopes with address block."""
    out_pdf = PdfFileWriter()

    w, h = landscape(C3)

    ksicht_contact_paragraph_style = ParagraphStyle(
        "Normal",
        fontName="Helvetica",
        fontSize=28,
        leading=32,
    )
    ksicht_contact_paragraph = Paragraph(
        "<br />".join(our_lines), style=ksicht_contact_paragraph_style
    )
    cw, ch = ksicht_contact_paragraph.wrap(620, 1000)

    for lines in recipient_lines:
        packet = io.BytesIO()
        can = canvas.Canvas(packet, pagesize=landscape(C3))
        paragraph_style = ParagraphStyle(
            "Normal",
            fontName="Helvetica",
            fontSize=38,
            leading=56,
            borderWidth=1,
            borderRadius=8,
            borderPadding=24,
            borderColor="#000",
        )
        paragraph = Paragraph("<br />".join(lines), style=paragraph_style)
        pw, ph = paragraph.wrap(700, 1000)
        paragraph.drawOn(can, w - pw - 48, 270)
        ksicht_contact_paragraph.drawOn(can, 24, h - 24 - ch)

        can.save()
        packet.seek(0)

        out_pdf.add_page(PdfFileReader(packet).pages[0])

    out_pdf.write(out_file)
    return out_file


def concatenate(in_files, out_file):
    """Merge all input PDF files into a single out file."""
    writer = PdfWriter()

    for f in in_files:
        writer.addpages(PdfReader(f).pages)

    writer.write(out_file)

    return out_file


def page_with_memo(x: int, y: int, label: str):
    packet = io.BytesIO()
    can = canvas.Canvas(packet, pagesize=A4)
    can.setFont("Helvetica", 24)
    can.drawString(x, y, label)
    can.save()
    packet.seek(0)
    return PdfFileReader(packet).pages[0]


def prepare_submission_for_export(in_file, label: str):
    """Prepare submission for exporting later on."""
    working_file = io.BytesIO()
    out_pdf = PdfFileWriter()

    # Make sure the PDF file is valid. If it isn't render a PDF with error message contained.
    try:
        in_pdf = PdfFileReader(in_file)
        out_pdf.append_pages_from_reader(in_pdf)
    except PdfReadError:  # noqa: F821
        out_pdf.add_page(page_with_memo(10, 200, "!! Tento PDF soubor je poškozený !!"))

    out_pdf.write(working_file)
    working_file.seek(0)

    # Write person label
    in_pdf = PdfFileReader(working_file)
    out_pdf = PdfFileWriter()
    memo_page = page_with_memo(10, 10, label)

    for pagenum in range(len(in_pdf.pages)):
        # add the "watermark" (which is the new pdf) on the existing page
        page = in_pdf.pages[pagenum]
        page.merge_page(memo_page)
        out_pdf.add_page(page)

    out_normal = out_pdf
    out_duplex = deepcopy(out_normal)

    # Ensure number of pages is even. Useful for duplex printing.
    if len(in_pdf.pages) % 2 == 1:
        out_duplex.add_blank_page()

    return out_normal, out_duplex
