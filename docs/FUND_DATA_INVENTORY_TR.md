# Türkiye Fon Verisi — Kaynak Envanteri ve Toplama Planı

İnceleme tarihi: 10 Temmuz 2026. Bu belge mühendislik ve kaynak riski
değerlendirmesidir; hukuk görüşü değildir. Açık kaynak kod ile kaynak verinin
yeniden dağıtım hakkı aynı şey değildir.

## Bugün toplayabildiklerimiz

| Veri | Kaynak | Sıklık | Yöntem | Durum |
|---|---|---:|---|---|
| Fon fiyatı/NAV | Kullanıcının TEFAS dışa aktarımı | İş günü | CSV/JSON içe aktar | Hazır |
| Fon toplam değeri, yatırımcı, pay, risk | Kullanıcının TEFAS dışa aktarımı | İş günü | Türkçe/İngilizce sütunlu CSV içe aktar | Hazır |
| Fon piyasası toplam büyüklüğü ve varlık dağılımı | SPK aylık istatistik bülteni | Aylık/gecikmeli | Resmî XLS indir, hashle, yerelde ayrıştır | Hazır |
| Emeklilik fonları toplam büyüklüğü ve dağılımı | SPK aylık istatistik bülteni | Aylık/gecikmeli | Resmî XLS indir, hashle, yerelde ayrıştır | Hazır |
| USD/TRY | TCMB EVDS | İş günü | Belgeli API | Hazır |
| TÜFE | TCMB EVDS/TÜİK | Aylık | Belgeli API/resmî bülten | Hazır |
| Mevduat faizi | TCMB EVDS | Haftalık | Belgeli API | Hazır |
| Politika faizi, piyasa beklentileri | TCMB EVDS | Toplantı/aylık | Belgeli API | Hazır |

SPK'nın 2026 Mayıs XLS dosyası incelendiğinde fon bazındaki günlük tabloların
TEFAS'a yönlendirdiği, konsolide yatırım ve emeklilik fonu tarihçesinin ise
2025 Eylül'den itibaren Takasbank KYP ekranına taşındığı görülmektedir. Bu nedenle
SPK XLS kolektörü tarihsel ve pazar-geneli analiz için yararlıdır; 2026 günlük fon
fiyatlarının yerine geçmez.

## İzin veya sözleşme bekleyen kaynaklar

| Veri | Kaynak | Neden bekliyor? | Güvenli geçici yol |
|---|---|---|---|
| Tüm fonların otomatik günlük fiyatı | TEFAS | Açık ve belgeli genel API/lisans bulunamadı | Kullanıcı dışa aktarımı |
| Güncel kategori bazlı portföy büyüklüğü | Takasbank KYP | İnteraktif site, “tüm hakları saklıdır”; otomasyon izni bulunamadı | Ekrandan kullanıcı dışa aktarımı/izin talebi |
| Fon portföy dağılım raporları | KAP | MKK, KAP veri yayın servisini veri ürünü olarak sunuyor | Belge bağlantısı + kullanıcı indirmesi + hash |
| Fon izahname, yatırımcı bilgi formu ve ücretler | KAP | Toplu veri hizmeti sözleşmeli; belgeler farklı formatlarda | Kullanıcının seçtiği belgeyi içe aktar |
| Portföy yönetim şirketi günlük fiyat sayfaları | PYŞ siteleri | Her kurumun şartı ve şeması farklı | Kurum bazında yazılı izin/şart incelemesi |
| BIST endeks karşılaştırmaları | Borsa İstanbul | Endeks ve piyasa verisi lisanslı | Lisans veya kullanıcı tarafından sağlanan veri |

## İhtiyacımız olan normalize veri modeli

### Fon kimliği

- `fund_code`, tam unvan, kategori/tür, kurucu/PYŞ, para birimi
- TEFAS/BEFAS/BYF durumu, nitelikli yatırımcı kısıtı
- risk değeri, yönetim ücreti, toplam gider oranı
- alış/satış valörü, işlem son saati, asgari işlem tutarı
- kaynak URL'si, geçerlilik tarihi ve belge hash'i

### Günlük gözlem

- değerleme tarihi ve birim pay fiyatı
- fon toplam değeri, tedavüldeki pay ve yatırımcı sayısı
- veri alınma zamanı, kaynak, ham dosya SHA-256 değeri
- düzeltme/revizyon işareti

### Aylık portföy dağılımı

- ters repo, Takasbank para piyasası, mevduat/katılma hesabı
- kamu/özel sektör borçlanma araçları ve kira sertifikaları
- hisse, yabancı menkul kıymet, kıymetli maden, diğer fonlar
- rapor dönemi, açıklama tarihi ve toplamın %100 kontrolü

## Para piyasası fonlarında özellikle izleyeceğimiz alanlar

1. Günlük ve 7/30/90 günlük bileşik getiri.
2. Stopaj sonrası kullanıcı net getirisi (oran kullanıcı girdisi olmalı).
3. Brüt/net mevduat ve TLREF'e göre fark.
4. Ters repo, mevduat, Takasbank para piyasası ve borçlanma aracı dağılımı.
5. Fon büyüklüğü ve tahmini net para girişi: `değer değişimi - fiyat getirisi etkisi`.
6. Yatırımcı sayısı değişimi ve kişi başına ortalama bakiye.
7. Yönetim ücreti/toplam gider ve kesintiler sonrası performans.
8. Likidite: alış-satış valörü, işlem son saati ve tatil kuralları.

## Diğer fon kategorilerinde eklenecek ölçüler

- Borçlanma araçları: vade/faiz hassasiyeti ve politika faizi senaryosu.
- Hisse yoğun: BIST lisanslı karşılaştırma verisi sağlandığında alfa, beta ve düşüş.
- Altın/kıymetli maden: gram altın, ons altın ve USD/TRY ayrıştırması.
- Yabancı hisse/teknoloji: fon getirisi, USD/TRY getirisi ve yabancı varlık getirisi ayrıştırması.
- Fon sepeti/değişken: aylık portföy kayması ve kategori yoğunlaşması.
- Serbest fon: yatırımcı uygunluğu, performans ücreti ve açıklama kapsamı farkı.
- BES: devlet katkısı etkisinden ayrı fon performansı ve kesinti varsayımları.

## Toplama takvimi

- Her iş günü 20:00 sonrası: kullanıcı TEFAS dışa aktarımını içe al, boş/0 fiyatı reddet.
- Ertesi sabah: eksik fonlar için yalnız kullanıcı kaynaklı dosya yenilemesi bekle.
- Haftalık: EVDS mevduat faizi, TLREF ve kur kıyaslarını güncelle.
- Aylık: TÜFE ve izinli portföy dağılımını ekle.
- SPK bülteni çıktığında: XLS'yi bir kez indir, SHA-256 ile sabitle, ham dosyayı Git'e koyma.
- KAP/TEFAS/KYP: yazılı izin gelmeden toplu ağ kolektörü çalıştırma.

## Sonraki uygulama sırası

1. Para piyasası fonları için kullanıcı dışa aktarım dosyasını içe almak.
2. Fon günlük raporunu mevduat, TLREF, TÜFE ve USD/TRY ile karşılaştırmak.
3. Portföy dağılımı manuel dosya şemasını eklemek.
4. Takasbank ve MKK'dan otomatik erişim/yeniden kullanım koşullarını yazılı almak.
5. İzin geldikçe taşıma katmanını açmak; analiz kodunu değiştirmemek.

## Resmî bağlantılar

- [SPK günlük istatistikler](https://spk.gov.tr/istatistikler/istatistiksel-veriler/gunluk-istatistikler)
- [SPK 2026 aylık istatistik bültenleri](https://spk.gov.tr/istatistikler/aylik-istatistik-bultenleri/2026-yili-istatistik-bultenleri)
- [SPK fon portföy değerleri kaynak sayfası](https://spk.gov.tr/kurumlar/fonlar/yatirim-fonlari/borsa-yatirim-fonlari/portfoy-degerleri)
- [Takasbank KYP](https://www.takasbank.com.tr/tr/istatistikler/kurumsal-yatirimci-portfoy-istatistikleri-kyp)
- [TEFAS](https://www.tefas.gov.tr/)
- [MKK KAP hizmeti](https://www.mkk.com.tr/kurumsal-yonetim-hizmetleri/kap-kamuyu-aydinlatma-platformu)
- [TCMB EVDS](https://evds3.tcmb.gov.tr/)
