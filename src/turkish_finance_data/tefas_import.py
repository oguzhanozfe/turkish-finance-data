import argparse
import csv
import hashlib
import io
import json
import math
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


REQUIRED = {"fund_code", "valuation_date", "price"}
ALIASES = {
    "fund_code": ("fund_code", "code", "FON KODU", "FON_KODU", "Fon Kodu"),
    "valuation_date": ("valuation_date", "date", "TARİH", "TARIH", "Tarih"),
    "price": ("price", "FİYAT", "FIYAT", "Fiyat", "Fiyat(TL)"),
    "fund_name": ("fund_name", "name", "FON ADI", "FON_ADI", "Fon Adı"),
    "category": ("category", "KATEGORİ", "KATEGORI", "Kategori"),
    "total_value": ("total_value", "TOPLAM DEĞER", "TOPLAM_DEGER", "Toplam Değer"),
    "investor_count": ("investor_count", "YATIRIMCI", "Yatırımcı"),
    "share_count": ("share_count", "PAY", "Pay"),
    "risk_value": ("risk_value", "RİSK", "RISK", "Risk"),
}


def _field(row: Dict[str, Any], canonical: str) -> Any:
    for name in ALIASES[canonical]:
        if name in row and row[name] not in (None, ""):
            return row[name]
    return None


def _parse_date(value: Any) -> date:
    text = str(value).strip()
    for pattern in ("%Y-%m-%d", "%d.%m.%Y", "%d/%m/%Y", "%d-%m-%Y"):
        try:
            return datetime.strptime(text, pattern).date()
        except ValueError:
            pass
    raise ValueError(f"unsupported valuation date: {text}")


def _optional_number(row: Dict[str, Any], name: str) -> Optional[float]:
    value = _field(row, name)
    if value in (None, ""):
        return None
    text = str(value).strip()
    if "," in text:
        text = text.replace(".", "").replace(",", ".")
    parsed = float(text)
    if not math.isfinite(parsed) or parsed < 0:
        raise ValueError(f"{name} must be finite and non-negative")
    return parsed


def parse_tefas_export(body: bytes, content_type: str) -> List[Dict]:
    """Validate user-supplied TEFAS observations without network collection."""
    if "csv" in content_type:
        text = body.decode("utf-8-sig")
        dialect = csv.Sniffer().sniff(text[:4096], delimiters=",;\t")
        rows = list(csv.DictReader(io.StringIO(text), dialect=dialect))
    else:
        value = json.loads(body)
        rows = value.get("observations", value) if isinstance(value, dict) else value
    if not isinstance(rows, list) or not rows:
        raise ValueError("empty TEFAS export")
    digest = hashlib.sha256(body).hexdigest()
    normalized = []
    for row in rows:
        values = {name: _field(row, name) for name in REQUIRED}
        missing = {name for name, value in values.items() if value in (None, "")}
        if missing:
            raise ValueError("missing fields: " + ", ".join(sorted(missing)))
        code = str(values["fund_code"]).strip().upper()
        observed = _parse_date(values["valuation_date"])
        price = float(str(values["price"]).replace(",", "."))
        if not code or not math.isfinite(price) or price <= 0:
            raise ValueError("fund code and price must be valid and positive")
        item: Dict[str, Any] = {
            "series_code": f"TEFAS:{code}",
            "observation_date": observed.isoformat(),
            "value": price,
            "frequency": "business-daily",
            "source": "Takasbank TEFAS; user-supplied export",
            "provenance_sha256": digest,
        }
        for name in ("fund_name", "category"):
            value = _field(row, name)
            if value not in (None, ""):
                item[name] = str(value).strip()
        for name in ("total_value", "investor_count", "share_count", "risk_value"):
            value = _optional_number(row, name)
            if value is not None:
                item[name] = int(value) if name in {"investor_count", "risk_value"} else value
        normalized.append(item)
    return normalized


def save_tefas_package(
    body: bytes, content_type: str, output_dir: Path, source_name: str
) -> Dict[str, Any]:
    rows = sorted(
        parse_tefas_export(body, content_type),
        key=lambda item: (item["series_code"], item["observation_date"]),
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    suffix = ".json" if "json" in content_type else ".csv"
    raw_path = output_dir / f"source-export{suffix}"
    normalized_path = output_dir / "fund-observations.json"
    manifest_path = output_dir / "manifest.json"
    raw_path.write_bytes(body)
    normalized_path.write_text(
        json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    manifest = {
        "source": "Takasbank TEFAS; user-supplied export",
        "source_name": source_name,
        "imported_at": datetime.now(timezone.utc).isoformat(),
        "provenance_sha256": hashlib.sha256(body).hexdigest(),
        "observation_count": len(rows),
        "fund_codes": sorted({row["series_code"].split(":", 1)[1] for row in rows}),
        "first_date": min(row["observation_date"] for row in rows),
        "last_date": max(row["observation_date"] for row in rows),
        "raw_path": str(raw_path),
        "normalized_path": str(normalized_path),
        "redistribution": "local-only user export",
    }
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return manifest


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Import a user-supplied TEFAS CSV/JSON export")
    parser.add_argument("--input", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args(argv)
    input_path = Path(args.input)
    content_type = "application/json" if input_path.suffix.lower() == ".json" else "text/csv"
    manifest = save_tefas_package(
        input_path.read_bytes(), content_type, Path(args.output_dir), input_path.name
    )
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
