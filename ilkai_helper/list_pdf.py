import os

def list_pdf_names(directory_path):
    # Dizin içindeki tüm dosyaları ve dizinleri al
    files = os.listdir(directory_path)
    # Sadece .pdf ile biten dosyaları al
    pdf_names = [f for f in files if f.endswith('.pdf')]
    return pdf_names[0]

# Örnek kullanım
# PDF dosyalarının adlarını listeleme
