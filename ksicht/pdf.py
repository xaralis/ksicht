import io

from django.conf import settings
from PyPDF2 import PdfFileMerger, PdfFileReader, PdfFileWriter
import reportlab
from reportlab.lib.pagesizes import A4, C3, landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph


__all__ = (
    "concatenate",
    "ensure_even_pages",
)

reportlab.rl_config.TTFSearchPath.append(str(settings.BASE_DIR) + "/fonts")
pdfmetrics.registerFont(TTFont("Helvetica", "Helvetica.ttf"))


def envelopes(recipient_lines, our_lines, out_file):
    """Generate envelopes with address block."""
    out_pdf = PdfFileWriter()

    w, h = landscape(C3)

    ksicht_contact_paragraph_style = ParagraphStyle(
        "Normal", fontName="Helvetica", fontSize=28, leading=32,
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

        out_pdf.addPage(PdfFileReader(packet).getPage(0))

    out_pdf.write(out_file)
    return out_file


def concatenate(in_files, out_file):
    """Merge all input PDF files into a single out file."""
    out_pdf = PdfFileMerger(strict=True)

    for f in in_files:
        out_pdf.append(f)

    out_pdf.write(out_file)

    return out_file


def ensure_even_pages(in_file, out_file):
    """Consume input PDF file and write new PDF file that always has even count of pages.

    Useful for duplex printing.
    """
    in_pdf = PdfFileReader(in_file)
    page_count = in_pdf.getNumPages()

    out_pdf = PdfFileWriter()
    out_pdf.appendPagesFromReader(in_pdf)

    if page_count % 2 == 1:
        out_pdf.addBlankPage()

    out_pdf.write(out_file)

    return out_file


def write_label_on_all_pages(text, in_file, out_file):
    packet = io.BytesIO()
    can = canvas.Canvas(packet, pagesize=A4)
    can.setFont("Helvetica", 24)
    can.drawString(10, 10, text)
    can.save()
    packet.seek(0)

    in_pdf = PdfFileReader(in_file)
    label_pdf = PdfFileReader(packet)
    out_pdf = PdfFileWriter()

    for pagenum in range(in_pdf.getNumPages()):
        # add the "watermark" (which is the new pdf) on the existing page
        page = in_pdf.getPage(pagenum)
        page.mergePage(label_pdf.getPage(0))
        out_pdf.addPage(page)

    out_pdf.write(out_file)
    return out_file
