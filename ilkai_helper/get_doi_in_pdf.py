
import pdfplumber
import re

def doi_from_pdf(pdf_path):
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                doi_matches = re.findall(r'\b(10[.][0-9]{4,}(?:[.][0-9]+)*/(?:(?!["&\'<>])\S)+)\b', text, re.IGNORECASE)
                if doi_matches:
                    return doi_matches[0]
    return None
 