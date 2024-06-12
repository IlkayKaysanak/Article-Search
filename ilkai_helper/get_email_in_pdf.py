import pdfplumber
import re

def extract_emails_from_pdf(pdf_path):
    emails = []
    email_pattern = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b')
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                found_emails = email_pattern.findall(text)
                emails.extend(found_emails)
    except Exception as e:
        print(f"Error reading PDF file: {e}")

    return emails
