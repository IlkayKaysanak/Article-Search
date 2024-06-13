import google.generativeai as genai

def ai_ref(ref):
    genai.configure(api_key="AIzaSyAIAnuKJ-vM_8tN3QcyeWVRx9BJ_B3HNxQ")

    model = genai.GenerativeModel('gemini-1.5-flash-latest')

    promtRef = """Dergilerin atıf sayılarının sağlıklı olarak tespit edilebilmesi kaynakların düzgün yazılmasıyla doğrudan ilişkilidir. Düzgün bir kaynak yazımında, makaleye ulaşabilirliği sağlayacak bilgiler tam ve doğru olarak yer almalıdır. Her derginin kaynak yazım kuralları için uluslararası düzeyde bir standart oluşturarak, makalelerinde bu standartları uygulaması bu açıdan önemlidir.
    Genel geçerliliği olan bir kaynak yazımında:
    Makalede bulunan yazar sayısı 6 veya daha az ise tüm yazarlar belirtilmeli, 7 veya daha fazla ise ilk 6 isim yazılıp “et al” eklenmelidir.
    Kongre bildirileri, kişisel deneyimler, basılmamış yayınlar, tezler ve internet adresleri kaynak olarak gösterilmemelidir.
    DOI tek kabul edilebilir online referans olmalıdır.
    Kaynakların yazımı için örnekler (noktalama işaretlerine dikkat edilmesi yazarlardan özellikle istenmelidir!) :
    Makale için; Yazar(lar)ın soyad(lar)ı ve isim(ler)inin baş harf(ler)i, makale ismi, dergi ismi, yıl, cilt, sayı, sayfa no.su belirtilmelidir.
    Örnek:
    Stephane A. Management of congenital cholesteatoma with otoendoscopic surgery: case report. Turkiye Klinikleri J Med Sci. 2010;30(2):803-7.
    Yukardaki bilgilere göre aşağıdaki gelen kaynakların düzenlenmeye ihtiyacı varsa düzenler misin? Sonrada liste halinde geri döndür.Sadece kaynakların listesini geri döndür başka yorum yapma düzelt ve listeyi ver ,başlıkta olmasın:
    """

    response = model.generate_content(promtRef+ref)
    return response.text
