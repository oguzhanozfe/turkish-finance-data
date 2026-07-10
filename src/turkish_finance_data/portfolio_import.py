import argparse
import csv
import hashlib
import io
import json
import math
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


ALIASES = {
    "fund_code": ("fund_code", "code", "FON KODU", "FON_KODU", "Fon Kodu"),
    "report_date": ("report_date", "date", "DÖNEM", "DONEM", "TARİH", "TARIH", "Tarih"),
    "asset_class": ("asset_class", "VARLIK TÜRÜ", "VARLIK TURU", "Varlık Türü"),
    "weight_pct": ("weight_pct", "ORAN", "ORAN (%)", "Oran", "AĞIRLIK", "AGIRLIK"),
}


def _field(row: Dict[str, Any], name: str) -> Any:
    return next((row[key] for key in ALIASES[name] if row.get(key) not in (None, "")), None)


def normalize_asset_class(value: Any) -> str:
    text = unicodedata.normalize("NFKD", str(value).strip().upper())
    ascii_text = "".join(character for character in text if not unicodedata.combining(character))
    return "_".join(part for part in "".join(
        character if character.isalnum() else " " for character in ascii_text
    ).split())


def _date(value: Any) -> str:
    text = str(value).strip()
    for pattern in ("%Y-%m-%d", "%d.%m.%Y", "%d/%m/%Y", "%d-%m-%Y"):
        try:
            return datetime.strptime(text, pattern).date().isoformat()
        except ValueError:
            pass
    raise ValueError(f"unsupported report date: {text}")


def _number(value: Any) -> float:
    text = str(value).strip().replace("%", "")
    if "," in text:
        text = text.replace(".", "").replace(",", ".")
    number = float(text)
    if not math.isfinite(number) or not 0 <= number <= 100:
        raise ValueError("portfolio weight must be between 0 and 100")
    return number


def parse_portfolio_export(body: bytes) -> List[Dict[str, Any]]:
    text = body.decode("utf-8-sig")
    dialect = csv.Sniffer().sniff(text[:4096], delimiters=",;\t")
    source_rows = list(csv.DictReader(io.StringIO(text), dialect=dialect))
    if not source_rows:
        raise ValueError("empty portfolio export")
    digest = hashlib.sha256(body).hexdigest()
    rows: List[Dict[str, Any]] = []
    totals: Dict[Tuple[str, str], float] = {}
    for row in source_rows:
        missing = [name for name in ALIASES if _field(row, name) in (None, "")]
        if missing:
            raise ValueError("missing fields: " + ", ".join(sorted(missing)))
        code = str(_field(row, "fund_code")).strip().upper()
        report_date = _date(_field(row, "report_date"))
        asset_label = str(_field(row, "asset_class")).strip()
        weight = _number(_field(row, "weight_pct"))
        if not code or not asset_label:
            raise ValueError("fund code and asset class are required")
        item = {
            "fund_code": code,
            "report_date": report_date,
            "asset_class": normalize_asset_class(asset_label),
            "asset_class_label": asset_label,
            "weight_pct": weight,
            "source": "user-supplied TEFAS/KAP portfolio export",
            "provenance_sha256": digest,
        }
        rows.append(item)
        key = (code, report_date)
        totals[key] = totals.get(key, 0.0) + weight
    invalid = {key: total for key, total in totals.items() if not 99 <= total <= 101}
    if invalid:
        details = ", ".join(f"{code}/{period}={total:.2f}%" for (code, period), total in invalid.items())
        raise ValueError("portfolio weights must total approximately 100%: " + details)
    return sorted(rows, key=lambda item: (item["fund_code"], item["report_date"], item["asset_class"]))


def save_portfolio_package(body: bytes, output_dir: Path, source_name: str) -> Dict[str, Any]:
    rows = parse_portfolio_export(body)
    output_dir.mkdir(parents=True, exist_ok=True)
    raw_path = output_dir / "source-portfolio.csv"
    normalized_path = output_dir / "portfolio-allocations.json"
    manifest_path = output_dir / "manifest.json"
    raw_path.write_bytes(body)
    normalized_path.write_text(
        json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    manifest = {
        "source": "user-supplied TEFAS/KAP portfolio export",
        "source_name": source_name,
        "imported_at": datetime.now(timezone.utc).isoformat(),
        "provenance_sha256": hashlib.sha256(body).hexdigest(),
        "allocation_rows": len(rows),
        "fund_codes": sorted({row["fund_code"] for row in rows}),
        "periods": sorted({row["report_date"] for row in rows}),
        "normalized_path": str(normalized_path),
        "redistribution": "local-only user export; link original disclosure",
    }
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return manifest


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Import user-supplied fund portfolio allocations")
    parser.add_argument("--input", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args(argv)
    path = Path(args.input)
    manifest = save_portfolio_package(path.read_bytes(), Path(args.output_dir), path.name)
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
