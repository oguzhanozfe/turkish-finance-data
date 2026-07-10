# Data source and reuse contract

Status reviewed on 2026-07-10. This is an engineering interpretation, not legal
advice. Obtain Turkish counsel for a public commercial service or redistribution
at scale.

Primary references:

- [TCMB EVDS terms of use](https://evds2.tcmb.gov.tr/help/videos/EVDS_Kullanim_Sartlari.pdf)
- [TCMB EVDS web-service guide](https://evds2.tcmb.gov.tr/help/videos/EVDS_Web_Servis_Kullanim_Kilavuzu.pdf)
- [TEFAS Fund Information Platform](https://www.tefas.gov.tr/)
- [Borsa İstanbul index licensing](https://www.borsaistanbul.com/en/indices/licensing-indices)
- [Borsa İstanbul market-data products](https://www.borsaistanbul.com/en/data/data-dissemination/market-data-products)

## TCMB EVDS — approved Phase 1 source

- Owner/publisher: Türkiye Cumhuriyet Merkez Bankası (TCMB).
- Access: authenticated EVDS web service; the user obtains a personal API key.
- Key handling: HTTP `key` header only. Never commit, persist, print, or place it
  in a URL.
- Reuse: EVDS terms state that data may be used and published by third parties
  with source attribution, including in commercial products without passing an
  extra data charge to product users.
- Required attribution: `Kaynak: Türkiye Cumhuriyet Merkez Bankası, EVDS` plus
  series code, observation date, and retrieval date.
- Caveat: some EVDS content originates with third parties; inspect series
  metadata before redistributing those specific series.

Useful Phase 1 families visible in EVDS:

- Türk Lirası Gecelik Referans Faiz Oranı (BIST-TLREF)
- Borsa İstanbul Gecelik Repo Faiz Oranları
- Açık Piyasa Repo ve Ters Repo İşlemleri
- Repo ve Ters Repo İşlemleri
- TL mevduat faiz oranları
- TÜFE and official exchange rates

The exact series code is configuration, not hard-coded policy. A series must be
approved in `sources.json` only after checking its current EVDS metadata,
frequency, unit, and upstream owner.

## TEFAS — permission required for automated collection

- Operator: Takasbank.
- Observed technical route: the 2026 public site calls a per-fund JSON endpoint
  and accepts fixed look-back values of 1, 3, 6, 12, 36, or 60 months.
- Observed behavior is not a contractual API guarantee.
- Takasbank publishes a disclaimer but no affirmative public-data license was
  located that authorizes automated collection or redistribution.
- Takasbank's documented operational TEFAS web services are for members and use
  member authentication.

Until written permission arrives:

1. Do not ship an enabled TEFAS network collector.
2. Do not bypass bot controls, impersonate browser TLS, solve CAPTCHAs, or rotate
   identities.
3. Accept user-provided TEFAS CSV/JSON exports and preserve provenance.
4. Do not commit or publish downloaded TEFAS price history in this repository.
5. Keep the parser independent from the transport so a permitted API can be
   enabled later without changing analytics.

If permission is granted, proposed load is deliberately small: user-selected
fund codes only, at most one request per fund per business day after NAV
publication, one retry the following morning, conditional requests/caching when
supported, and immediate backoff on 403/429/5xx responses.

## Borsa İstanbul — licensing review required

Borsa İstanbul states that it owns intellectual-property rights in BIST indices
and market data, sells data products, and requires licenses for specified index
and benchmark uses. Do not redistribute BIST index histories or market feeds
from this project without the applicable agreement or written confirmation.

For Phase 1, use EVDS series whose terms permit reuse, retain TCMB attribution,
and flag any series metadata that identifies Borsa İstanbul as the upstream
owner for an additional rights review.

## KAP — Phase 2

KAP disclosures are public, but public availability does not by itself grant a
bulk redistribution license. Phase 2 should fetch only document metadata and
user-requested disclosures after reviewing MKK/KAP data-product terms. Original
documents should be linked and hashed rather than republished by default.

MKK's current product catalogue explicitly describes the KAP data publication
service as a channel used by data vendors, and its 2024 activity report refers
to data-sale packages. Treat bulk KAP transport as a contracted data product.

## SPK monthly statistics — approved for local collection

- Publisher: Sermaye Piyasası Kurulu (SPK).
- Access: direct, publicly linked `.xls` workbooks with no hidden endpoint or
  authentication bypass.
- Content: delayed monthly aggregate statistics for mutual and pension funds,
  plus wider capital-markets tables.
- Collector policy: fetch each published workbook once, validate the legacy XLS
  signature, store source URL/retrieval time/SHA-256, and keep raw files local.
- Redistribution: publish code and attributed derived analysis; do not commit or
  mirror raw SPK workbooks until reuse terms are confirmed in writing.
- Limitation: inspected 2026 workbooks refer fund-level daily data to TEFAS and
  move aggregate fund history from September 2025 onward to Takasbank KYP.

See [docs/FUND_DATA_INVENTORY_TR.md](docs/FUND_DATA_INVENTORY_TR.md) for the
field-level source matrix and collection schedule.
