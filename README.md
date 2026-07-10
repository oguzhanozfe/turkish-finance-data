# Turkish Finance Data

A small, local-first Python toolkit for reproducible Turkish market research.
Phase 1 covers legally documented TCMB EVDS web-service access and validated
manual TEFAS fund-price imports.

The repository contains code, schemas, tests, and source metadata. It does not
redistribute market datasets, credentials, or investment recommendations.

## Why the source boundary matters

- **TCMB EVDS:** enabled. EVDS permits web-service access and third-party use or
  publication with attribution. Each user supplies their own free API key.
- **TEFAS:** manual import only until Takasbank gives written permission for
  automated use and redistribution of its public website JSON responses.
- **Borsa İstanbul index/market data:** excluded from Phase 1. Borsa İstanbul
  asserts intellectual-property rights and provides licensing routes for data
  products and benchmark use.

Open-source code does not make upstream data open data. The MIT license in this
repository applies only to this repository's code.

## Install and test

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

No third-party Python package is required.

## EVDS usage

Create a free EVDS account, obtain an API key, and keep it outside the repository:

```bash
export EVDS_API_KEY='your-local-key'
python3 -m turkish_finance_data.evds \
  --series SERIES_CODE \
  --start 01-07-2026 \
  --end 10-07-2026
```

The key is sent in the HTTP `key` header as required by the current EVDS guide;
it is never placed in the URL or logs.

EVDS3 time-series requests use the `/igmevdsms-dis` service path. The legacy
EVDS2 service URL now redirects to the EVDS3 web application and must not be
used as an API base URL.

## 2026 USD/TRY scenario report

Generate the reproducible 30-line report from the first 2026 observation to
10 July. The macro snapshot is dated 10 July 2026 and the forecast is a
scenario range, not a promise or personal investment recommendation.

The companion [detailed Turkish report](reports/usdtry-2026-07-10-detayli.md)
explains the inflation, real-rate, external-balance, reserve, micro-flow, and
current political/geopolitical transmission channels behind the range.

```bash
PYTHONPATH=src python3 -m turkish_finance_data.usdtry_report \
  --as-of 10-07-2026 \
  --output reports/usdtry-2026-07-10.md
```

## Collection cadence

| Dataset | Native frequency | Collector policy |
|---|---:|---|
| TLREF and overnight repo rates | Business daily | Check once after the EVDS release calendar indicates publication |
| TCMB repo/ters-repo operations | Business daily/weekly depending on series | Preserve the series' native frequency; do not forward-fill raw data |
| TL deposit rates | Weekly | Fetch once after weekly publication |
| CPI | Monthly | Fetch only after the scheduled monthly release |
| TEFAS fund unit prices | Valuation/business daily for most funds | Manual import; later, if permitted, one request per watched fund after publication plus one next-morning retry |
| KAP portfolio-allocation reports | Usually monthly | Phase 2; ingest disclosures by their reporting period, not by scrape time |

Every observation must preserve its observation date, retrieval timestamp,
source identifier, native frequency, and SHA-256 provenance hash.

See [DATA_SOURCES.md](DATA_SOURCES.md) for the legal/data contract and
[docs/TEFAS_PERMISSION_REQUEST_TR.md](docs/TEFAS_PERMISSION_REQUEST_TR.md) for
the permission request to Takasbank.

## Not investment advice

This software retrieves and validates public statistical data. It does not know
the user's tax position, liquidity needs, eligibility, time horizon, or loss
tolerance and must not label a product as universally “best.”
