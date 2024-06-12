
#Sağlıklı Çalışlmıyo!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

def find_specialty(text):
    specialties = set()
    specialties_list = [
        "Cardiology", "Kardiyoloji",
        "Neurology", "Nöroloji",
        "Oncology", "Onkoloji",
        "Pediatrics", "Pediatri",
        "Surgery", "Cerrahi",
        "Radiology", "Radyoloji",
        "Pathology", "Patoloji",
        "Dermatology", "Dermatoloji",
        "Endocrinology", "Endokrinoloji",
        "Gastroenterology", "Gastroenteroloji",
        "Hematology", "Hematoloji",
        "Nephrology", "Nefroloji",
        "Orthopedics", "Ortopedi",
        "Psychiatry", "Psikiyatri",
        "Rheumatology", "Romatoloji",
        "Urology", "Üroloji",
        "Ophthalmology", "Göz Hastalıkları",
        "Anesthesiology", "Anesteziyoloji",
        "Allergy", "Alerji",
        "Immunology", "İmmünoloji",
        "Infectious Disease", "Enfeksiyon Hastalıkları",
        "Pulmonology", "Göğüs Hastalıkları",
        "Radiation Oncology", "Radyasyon Onkolojisi",
        "Sports Medicine", "Spor Hekimliği",
        "Vascular Surgery", "Vasküler Cerrahi"
    ]
    
    specialty_pattern = re.compile(r"\b(" + "|".join(specialties_list) + r")\b", re.IGNORECASE)
    
    
    specialty_matches = specialty_pattern.findall(text)
    for match in specialty_matches:
        specialties.add(match.strip())
    
    return specialties