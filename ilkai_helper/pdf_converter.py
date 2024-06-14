import fitz 

def pdf_to_text(path):
    pdf_document = fitz.open(path)

    text = ""
    for page_num in range(pdf_document.page_count):
        page = pdf_document[page_num]
        text += page.get_text()

    return text
