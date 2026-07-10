# Takasbank'a TEFAS veri kullanım izni talebi

Gönderim için önerilen adres: `tefasp@takasbank.com.tr`

**Konu:** TEFAS Fon Bilgilendirme verileri için düşük frekanslı açık kaynak erişim izni

Merhaba,

Kişisel yatırım araştırması amacıyla geliştirilen, alım-satım emri iletmeyen ve
banka kimlik bilgisi toplamayan açık kaynak bir yazılım üzerinde çalışıyoruz.
Yazılım yalnızca kullanıcının seçtiği az sayıdaki fonun yayımlanmış birim pay
fiyatlarını günlük olarak karşılaştırmayı amaçlamaktadır.

TEFAS Fon Bilgilendirme Platformu'nun web uygulamasında kullanılan fon bazlı
JSON servislerinin aşağıdaki koşullarda kullanımına izin verilip verilmediğini
yazılı olarak teyit etmek istiyoruz:

1. Her izlenen fon için iş günü başına en fazla bir sorgu yapılması,
2. Yanıtların yalnızca kullanıcının yerel cihazında önbelleğe alınması,
3. Kaynak olarak Takasbank/TEFAS ve veri tarihinin açıkça gösterilmesi,
4. Bot koruması, CAPTCHA veya erişim sınırlamasının hiçbir şekilde aşılmaması,
5. Yazılım kodunun MIT lisansıyla GitHub üzerinde yayımlanması,
6. Ham TEFAS veri setinin GitHub deposunda veya ayrı bir servis üzerinden yeniden
   dağıtılmaması.

Özellikle şu konularda yönlendirmenizi rica ederiz:

- Bireysel ve açık kaynak kullanım için önerilen resmi API/servis var mıdır?
- Web uygulamasının kullandığı `/api/funds/...` servislerine otomatik erişim
  izinli midir?
- İzinliyse hız limiti, önbellek süresi ve zorunlu kaynak gösterimi nedir?
- Kullanıcının kendi cihazında tarihsel veri saklaması ve türetilmiş getiri/risk
  metrikleri hesaplaması izinli midir?
- Ham veri paylaşılmadan yalnızca yazılım kodunun yayımlanması için ayrıca bir
  sözleşme gerekir mi?

Yazılı izniniz veya önerdiğiniz veri sözleşmesi olmadan otomatik TEFAS erişimini
genel kullanıma açmayacağız.

Teşekkür ederiz.
