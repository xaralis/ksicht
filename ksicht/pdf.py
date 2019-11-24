from PyPDF2 import PdfFileMerger, PdfFileReader, PdfFileWriter


__all__ = (
    "concatenate",
    "ensure_even_pages",
)


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
