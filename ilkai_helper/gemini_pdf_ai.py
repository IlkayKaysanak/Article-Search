import json
import google.generativeai as genai

def ai_ref2(text):
    genai.configure(api_key="AIzaSyAIAnuKJ-vM_8tN3QcyeWVRx9BJ_B3HNxQ")

    model = genai.GenerativeModel('gemini-1.5-flash-latest')

    jsonformatım2 ="""
                            "journalName": ,
                            "articleType": ,
                            "articleDOI": ,
                            "articleCode": ,
                            "articleYear": ,
                            "articleVolume": ,
                            "articleIssue": ,
                            "articlePageRange":,
                            "articleTitle": {"TR": ,
                                             "ENG": },
                            "articleAbstracts": {"TR": ,
                                                 "ENG":},
                            "articleKeywords": {"TR": ,
                                                "ENG":
                                                },
                            "articleAuthors": {"Name":,
                                                "fullSpeciality:,
                                                "isCorrespondence":,
                                                "email": 
                                                },
                            "articleReferences": [ {
                                                "Yazarlar":,
                                                "Makale İsmi": ,
                                                "Dergi İsmi":,
                                                "Yıl":,
                                                "Cilt":,
                                                "Sayı":,
                                                "Sayfa No":
                                            },],
                            "mergedReferences":,                
                            "articleURL": ,
"""
    atifRules = """Dergilerin atıf sayılarının sağlıklı olarak tespit edilebilmesi kaynakların düzgün yazılmasıyla doğrudan ilişkilidir. Düzgün bir kaynak yazımında, makaleye ulaşabilirliği sağlayacak bilgiler tam ve doğru olarak yer almalıdır. Her derginin kaynak yazım kuralları için uluslararası düzeyde bir standart oluşturarak, makalelerinde bu standartları uygulaması bu açıdan önemlidir.
    Genel geçerliliği olan bir kaynak yazımında:
    Makalede bulunan yazar sayısı 6 veya daha az ise tüm yazarlar belirtilmeli, 7 veya daha fazla ise ilk 6 isim yazılıp “et al” eklenmelidir.
    Kongre bildirileri, kişisel deneyimler, basılmamış yayınlar, tezler ve internet adresleri kaynak olarak gösterilmemelidir.
    DOI tek kabul edilebilir online referans olmalıdır.
    Kaynakların yazımı için örnekler (noktalama işaretlerine dikkat edilmesi yazarlardan özellikle istenmelidir!) :
    Makale için; Yazar(lar)ın soyad(lar)ı ve isim(ler)inin baş harf(ler)i, makale ismi, dergi ismi, yıl, cilt, sayı, sayfa no.su belirtilmelidir.
    Örnek:
    Stephane A. Management of congenital cholesteatoma with otoendoscopic surgery: case report. Turkiye Klinikleri J Med Sci. 2010;30(2):803-7.
    """
    response = model.generate_content(f"Metinde verceğim kısım bir akadamik makale ben senin bu makaleyi okuyup bana şu şekilde json formatında döndürmeni istiyorum. {jsonformatım2} Formatımın başlıkları ve düzeni bu düzenini bozmadan doldurup bana bir dizi olarak geri döndür. . Metin : {text}  ")

    try:
        if response and response.text:
            def remove_code_blocks(text):
                # Remove ```json block
                text = text.replace('```json', '')
                # Remove ```
                text = text.replace('```', '')
                return text.strip()
            fixed_text = remove_code_blocks(response.text)
            data = json.loads(fixed_text)
            return data
        else:
            print("Error: Empty or invalid response.")
            return None
    except Exception as e:
        print(f"Error text: {e}")