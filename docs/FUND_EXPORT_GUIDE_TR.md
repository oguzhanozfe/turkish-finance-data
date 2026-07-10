# TEFAS/KAP Fon Verisi Dışa Aktarma Rehberi

Otomatik TEFAS kolektörü izin beklerken günlük fon verisini güvenli biçimde
kullanmanın yolu, kullanıcının seçtiği veriyi dışa aktarıp yerel içe aktarıcıya
vermektir.

## Günlük fon bilgileri

1. TEFAS `Tarihsel Veriler` ekranını açın.
2. Fon türünü ve tarih aralığını seçin; ilk deneme için yalnız takip edeceğiniz
   para piyasası fonlarını seçin.
3. Genel bilgiler tablosunu Excel/CSV olarak dışa aktarın.
4. Excel dosyası geldiyse UTF-8 CSV olarak kaydedin.
5. Dosyayı örneğin `data/inbox/tefas-genel.csv` yoluna koyun.
6. Aşağıdaki komutu çalıştırın:

```bash
PYTHONPATH=src python3 -m turkish_finance_data.tefas_import \
  --input data/inbox/tefas-genel.csv \
  --output-dir data/funds/daily
```

İçe aktarıcı Türkçe ve İngilizce sütunları kabul eder. Asgari alanlar:

```text
FON KODU;TARİH;FİYAT
```

İsteğe bağlı alanlar:

```text
FON ADI;KATEGORİ;TOPLAM DEĞER;YATIRIMCI;PAY;RİSK
```

## Portföy dağılımı

TEFAS tarihsel verilerde `Portföy Dağılımı` sekmesinden veya KAP'taki seçili
fonun portföy dağılım raporundan veriyi şu uzun formata getirin:

```text
FON KODU;DÖNEM;VARLIK TÜRÜ;ORAN
PPF;30.06.2026;Ters Repo;55,5
PPF;30.06.2026;Takasbank Para Piyasası;44,5
```

Ardından:

```bash
PYTHONPATH=src python3 -m turkish_finance_data.portfolio_import \
  --input data/inbox/portfoy-dagilimi.csv \
  --output-dir data/funds/portfolio
```

Dağılım toplamı her fon ve dönem için %99–101 aralığında değilse dosya
reddedilir. Ham dosya, normalize JSON ve SHA-256 manifesti `data/` altında kalır
ve Git'e girmez.
