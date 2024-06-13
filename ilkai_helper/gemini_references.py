import google.generativeai as genai

def ai_ref(ref):
    genai.configure(api_key="AIzaSyAIAnuKJ-vM_8tN3QcyeWVRx9BJ_B3HNxQ")

    model = genai.GenerativeModel('gemini-1.5-flash-latest')

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
    promtRef = """Yukarda verdiğim bilgilere göre gelen referansları düzenleyebiliyorsan formatlarını düzenle, düzenleyecek bilgi yok ise olduğu haliyle bırak. Başlık yorum yapmadan bana sadece kaynakları listele. Sadece kaynakların dönmüş hali lazım bana. Ve Kendin herhangi bir şey sakın ekleme sadece formatını elindeki bilgilerle düzenle bilgi yoksa formatın o kısmı boş kalsın.Düzenlenmiyor ve hatalı ise de kaldırır mısın.:
"""
    response = model.generate_content(atifRules+promtRef+ref)
    return response.text
