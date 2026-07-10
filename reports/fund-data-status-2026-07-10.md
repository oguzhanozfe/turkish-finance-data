# Fon Verisi Durum Raporu — 10 Temmuz 2026

## Sonuç

Fon aşamasının kaynak ve içe aktarma altyapısı hazırdır. Üç bağımsız veri yolu
kuruldu:

1. TCMB EVDS'den otomatik kıyas verileri.
2. SPK'nın resmî aylık XLS bültenlerinden yerel, hash'li pazar verisi.
3. Kullanıcının TEFAS/KAP dışa aktarımlarından günlük fon ve portföy dağılımı.

## Gerçekten toplanan veri

SPK Mayıs 2026 aylık bülteni 10 Temmuz'da toplandı:

- Kaynak dosya: `Aylik_istatistik_bulteni_2026_05.xls`
- Boyut: 1.248.256 bayt
- SHA-256: `cc95dbb6f2c400f4e4ae46708d1a1e6cee1d9b6d405154ed8edc70f4fd55d201`
- Yerel paket: `data/spk/2026-05/`
- Ham ve normalize veri `.gitignore` kapsamında; GitHub'a yüklenmez.

Dosya 2026 Mayıs bülteni olsa da fon konsolide tablolarının son dönemi 2025
Ağustos'tur. SPK tablosu 2025 Eylül'den sonraki veriler için Takasbank KYP'ye
yönlendirmektedir.

### Son SPK yatırım fonu gözlemi — Ağustos 2025

| Ölçü | Değer |
|---|---:|
| Fon sayısı | 1.868 |
| Toplam değer | 6.334.406,733 milyon TL |
| Yatırımcı sayısı | 6.608.768 |
| Vadeli mevduat | %26,58 |
| Yabancı menkul kıymet | %22,06 |
| Ters repo | %21,07 |
| Hisse senedi | %10,08 |
| Kamu borçlanma aracı | %5,89 |
| Fon katılma payı | %4,24 |
| Özel sektör borçlanma aracı | %3,76 |
| Kıymetli maden | %3,30 |
| Para piyasası | %1,17 |
| Diğer | %1,84 |

### Son SPK emeklilik fonu gözlemi — Ağustos 2025

| Ölçü | Değer |
|---|---:|
| Fon sayısı | 396 |
| Toplam değer | 1.715.374,240 milyon TL |
| Yatırımcı sayısı | 9.896.149 |
| Kıymetli maden | %34,74 |
| Hisse senedi | %21,58 |
| Kamu borçlanma aracı | %16,59 |
| Fon katılma payı | %7,00 |
| Yabancı menkul kıymet | %6,16 |
| Ters repo | %5,85 |
| Vadeli mevduat | %3,71 |

## Bugün alınabilen alanlar

| Alan | Hazır mı? | Kaynak/yöntem |
|---|---|---|
| Günlük fon fiyatı | Evet | Kullanıcı TEFAS CSV/JSON dışa aktarımı |
| Fon adı ve kategori | Evet | Kullanıcı dışa aktarımı |
| Fon toplam değeri | Evet | Kullanıcı dışa aktarımı |
| Yatırımcı/pay/risk değeri | Evet | Kullanıcı dışa aktarımı |
| Aylık portföy dağılımı | Evet | Kullanıcı TEFAS/KAP CSV içe aktarımı |
| SPK tarihsel pazar toplamı | Evet | Otomatik resmî XLS kolektörü |
| Mevduat, USD/TRY, TÜFE | Evet | TCMB EVDS |
| Günlük tüm fonları otomatik çekme | Hayır | Takasbank yazılı izni bekleniyor |
| KAP toplu belge akışı | Hayır | MKK veri yayın sözleşmesi gerekiyor |
| BIST endeks geçmişi | Hayır | Borsa İstanbul lisansı gerekiyor |

## Para piyasası fonu raporu için gereken ilk dosya

TEFAS `Tarihsel Veriler` ekranından takip edilecek para piyasası fonlarının
1 Ocak–10 Temmuz 2026 genel bilgi tablosunu CSV olarak dışa aktarın. Asgari
sütunlar:

```text
FON KODU;TARİH;FİYAT
```

Mümkünse şu alanları da ekleyin:

```text
FON ADI;KATEGORİ;TOPLAM DEĞER;YATIRIMCI;PAY;RİSK
```

Bu dosya geldiğinde her fon için günlük/7/30/90 günlük getiri, azami düşüş,
mevduat farkı, USD/TL farkı, TÜFE farkı, fon büyümesi ve tahmini para akışı
hesaplanabilir.

## Sıradaki teknik çıktı

İlk gerçek TEFAS dışa aktarımı içeri alındıktan sonra üretilecek günlük rapor:

- En yüksek günlük ve 30 günlük para piyasası fonu getirileri.
- Brüt ve kullanıcı stopaj oranına göre net mevduat karşılaştırması.
- Fon toplam değeri artışının fiyat getirisi ve tahmini net giriş ayrımı.
- Fonun repo/mevduat/para piyasası ağırlığı.
- USD/TRY ve beklenen/gerçekleşen TÜFE karşılaştırması.
- Eksik gün, sıfır fiyat, geç açıklama ve sıra dışı büyüklük kontrolleri.

Kaynak ve komut ayrıntıları:

- [Fon veri envanteri](../docs/FUND_DATA_INVENTORY_TR.md)
- [Dışa aktarma rehberi](../docs/FUND_EXPORT_GUIDE_TR.md)
- [SPK aylık istatistikleri](https://spk.gov.tr/istatistikler/aylik-istatistik-bultenleri/2026-yili-istatistik-bultenleri)
