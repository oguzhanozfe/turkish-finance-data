import csv
import hashlib
import io
import json
import math
from datetime import date
from typing import Dict, List


REQUIRED = {"fund_code", "valuation_date", "price"}


def parse_tefas_export(body: bytes, content_type: str) -> List[Dict]:
    """Validate user-supplied TEFAS observations without network collection."""
    if "csv" in content_type:
        rows = list(csv.DictReader(io.StringIO(body.decode("utf-8-sig"))))
    else:
        value = json.loads(body)
        rows = value.get("observations", value) if isinstance(value, dict) else value
    if not isinstance(rows, list) or not rows:
        raise ValueError("empty TEFAS export")
    digest = hashlib.sha256(body).hexdigest()
    normalized = []
    for row in rows:
        missing = REQUIRED - set(row)
        if missing:
            raise ValueError("missing fields: " + ", ".join(sorted(missing)))
        code = str(row["fund_code"]).strip().upper()
        observed = date.fromisoformat(str(row["valuation_date"]))
        price = float(str(row["price"]).replace(",", "."))
        if not code or not math.isfinite(price) or price <= 0:
            raise ValueError("fund code and price must be valid and positive")
        normalized.append({
            "series_code": f"TEFAS:{code}",
            "observation_date": observed.isoformat(),
            "value": price,
            "frequency": "business-daily",
            "source": "Takasbank TEFAS; user-supplied export",
            "provenance_sha256": digest,
        })
    return normalized
