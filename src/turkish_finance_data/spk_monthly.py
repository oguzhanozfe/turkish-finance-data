import argparse
import hashlib
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse
from urllib.request import Request, urlopen


OLE_XLS_SIGNATURE = bytes.fromhex("D0CF11E0A1B11AE1")
MAX_DOWNLOAD_BYTES = 20 * 1024 * 1024
ALLOWED_HOSTS = {"spk.gov.tr", "www.spk.gov.tr"}


class SpkMonthlyError(RuntimeError):
    pass


@dataclass(frozen=True)
class SpkMonthlyResponse:
    source_url: str
    retrieved_at: str
    provenance_sha256: str
    body: bytes


class SpkMonthlyClient:
    """Download an explicitly published SPK monthly-statistics workbook."""

    def __init__(self, opener=urlopen):
        self._opener = opener

    @staticmethod
    def _validate_url(url: str) -> None:
        parsed = urlparse(url)
        if parsed.scheme != "https" or parsed.hostname not in ALLOWED_HOSTS:
            raise ValueError("URL must be an HTTPS spk.gov.tr address")
        if not parsed.path.lower().endswith(".xls"):
            raise ValueError("SPK monthly source must be an .xls workbook")

    def fetch(self, url: str) -> SpkMonthlyResponse:
        self._validate_url(url)
        request = Request(url, headers={
            "Accept": "application/vnd.ms-excel",
            "User-Agent": "turkish-finance-data/0.2",
        })
        try:
            with self._opener(request, timeout=60) as response:
                final_url = response.geturl() if hasattr(response, "geturl") else url
                self._validate_url(final_url)
                body = response.read(MAX_DOWNLOAD_BYTES + 1)
        except Exception as exc:
            raise SpkMonthlyError(str(exc)) from exc
        if len(body) > MAX_DOWNLOAD_BYTES:
            raise SpkMonthlyError("SPK workbook exceeds the 20 MiB safety limit")
        if not body.startswith(OLE_XLS_SIGNATURE):
            raise SpkMonthlyError("SPK response is not a legacy Excel workbook")
        return SpkMonthlyResponse(
            source_url=final_url,
            retrieved_at=datetime.now(timezone.utc).isoformat(),
            provenance_sha256=hashlib.sha256(body).hexdigest(),
            body=body,
        )


ALLOCATION_FIELDS = [
    "stocks_pct",
    "public_debt_pct",
    "reverse_repo_pct",
    "money_market_pct",
    "foreign_securities_pct",
    "corporate_bonds_pct",
    "term_deposit_pct",
    "precious_metals_pct",
    "fund_participation_shares_pct",
    "other_pct",
]


def _optional_float(value: Any) -> Optional[float]:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def extract_aggregate_sheet(sheet: Any, dataset: str, source_sheet: str) -> List[Dict[str, Any]]:
    """Normalize historical aggregate rows from SPK sheets III-1-5/III-2-2."""
    output: List[Dict[str, Any]] = []
    for row_index in range(sheet.nrows):
        year_value = sheet.cell_value(row_index, 0)
        month_value = sheet.cell_value(row_index, 1)
        if not isinstance(year_value, (int, float)):
            continue
        year = int(year_value)
        match = re.match(r"\s*(\d{1,2})", str(month_value))
        if year < 1900 or not match:
            continue
        month = int(match.group(1))
        if not 1 <= month <= 12:
            continue
        fund_count = _optional_float(sheet.cell_value(row_index, 2))
        nav = _optional_float(sheet.cell_value(row_index, 3))
        investors = _optional_float(sheet.cell_value(row_index, 4))
        if fund_count is None or nav is None:
            continue
        allocations = {
            field: _optional_float(sheet.cell_value(row_index, 5 + index))
            for index, field in enumerate(ALLOCATION_FIELDS)
        }
        output.append({
            "dataset": dataset,
            "period": f"{year:04d}-{month:02d}",
            "fund_count": int(fund_count),
            "net_asset_value_million_try": nav,
            "investor_count": int(investors) if investors is not None else None,
            "allocations": allocations,
            "source": "Sermaye Piyasası Kurulu Aylık İstatistik Bülteni",
            "source_sheet": source_sheet,
            "frequency": "monthly",
        })
    return output


def parse_spk_monthly(body: bytes) -> Dict[str, List[Dict[str, Any]]]:
    try:
        import xlrd
    except ImportError as exc:
        raise SpkMonthlyError("XLS parsing requires: pip install 'turkish-finance-data[xls]'") from exc
    try:
        workbook = xlrd.open_workbook(file_contents=body, on_demand=True)
        mutual = extract_aggregate_sheet(
            workbook.sheet_by_name("III-1-5"), "mutual_funds", "III-1-5"
        )
        pension = extract_aggregate_sheet(
            workbook.sheet_by_name("III-2-2"), "pension_funds", "III-2-2"
        )
    except Exception as exc:
        raise SpkMonthlyError(f"cannot parse SPK workbook: {exc}") from exc
    return {"mutual_funds": mutual, "pension_funds": pension}


def save_package(response: SpkMonthlyResponse, output_dir: Path, parse: bool = True) -> Dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    raw_path = output_dir / "spk-monthly.xls"
    manifest_path = output_dir / "manifest.json"
    normalized_path = output_dir / "aggregate-funds.json"
    raw_path.write_bytes(response.body)
    manifest: Dict[str, Any] = {
        "source": "Sermaye Piyasası Kurulu Aylık İstatistik Bülteni",
        "source_url": response.source_url,
        "retrieved_at": response.retrieved_at,
        "provenance_sha256": response.provenance_sha256,
        "bytes": len(response.body),
        "raw_path": str(raw_path),
        "redistribution": "raw workbook is local-only; publish code and derived analysis with attribution",
    }
    if parse:
        normalized = parse_spk_monthly(response.body)
        normalized_path.write_text(
            json.dumps(normalized, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        manifest["normalized_path"] = str(normalized_path)
        manifest["latest_periods"] = {
            key: rows[-1]["period"] if rows else None for key, rows in normalized.items()
        }
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return manifest


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Collect an official SPK monthly XLS workbook")
    parser.add_argument("--url", required=True, help="direct spk.gov.tr .xls URL")
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--no-parse", action="store_true")
    args = parser.parse_args(argv)
    response = SpkMonthlyClient().fetch(args.url)
    manifest = save_package(response, Path(args.output_dir), parse=not args.no_parse)
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
