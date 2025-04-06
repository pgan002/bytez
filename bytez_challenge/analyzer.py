from io import BytesIO

import PyPDF2


def analyze(content: BytesIO) -> list[str]:
    pdf = PyPDF2.PdfReader(content)
    return [page.extract_text() for page in pdf.pages]
