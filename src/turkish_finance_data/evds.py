import argparse
import hashlib
import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from urllib.parse import quote
from urllib.request import Request, urlopen


class EvdsError(RuntimeError):
    pass


@dataclass(frozen=True)
class EvdsResponse:
    series: List[str]
    retrieved_at: str
    provenance_sha256: str
    payload: Any


class EvdsClient:
    """Minimal EVDS client that keeps the personal API key out of URLs/logs."""

    base_url = "https://evds2.tcmb.gov.tr/service/evds"

    def __init__(self, api_key: str, opener=urlopen):
        if not api_key or not api_key.strip():
            raise ValueError("EVDS API key is required")
        self._api_key = api_key.strip()
        self._opener = opener

    def fetch(self, series: List[str], start: str, end: str) -> EvdsResponse:
        clean = [item.strip().upper() for item in series if item.strip()]
        if not clean or len(clean) > 20:
            raise ValueError("series must contain 1..20 EVDS series codes")
        for value, label in ((start, "start"), (end, "end")):
            try:
                datetime.strptime(value, "%d-%m-%Y")
            except ValueError as exc:
                raise ValueError(f"{label} must use DD-MM-YYYY") from exc
        series_path = "-".join(quote(code, safe=".") for code in clean)
        url = f"{self.base_url}/series={series_path}&startDate={start}&endDate={end}&type=json"
        request = Request(url, headers={
            "Accept": "application/json",
            "User-Agent": "turkish-finance-data/0.1",
            "key": self._api_key,
        })
        try:
            with self._opener(request, timeout=30) as response:
                raw = response.read()
        except Exception as exc:
            raise EvdsError(str(exc)) from exc
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise EvdsError("EVDS returned non-JSON content") from exc
        return EvdsResponse(
            series=clean,
            retrieved_at=datetime.now(timezone.utc).isoformat(),
            provenance_sha256=hashlib.sha256(raw).hexdigest(),
            payload=payload,
        )


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Fetch attributed TCMB EVDS series")
    parser.add_argument("--series", action="append", required=True)
    parser.add_argument("--start", required=True, help="DD-MM-YYYY")
    parser.add_argument("--end", required=True, help="DD-MM-YYYY")
    args = parser.parse_args(argv)
    key = os.environ.get("EVDS_API_KEY", "")
    if not key:
        parser.error("EVDS_API_KEY is not set")
    result = EvdsClient(key).fetch(args.series, args.start, args.end)
    print(json.dumps({
        "source": "Türkiye Cumhuriyet Merkez Bankası, EVDS",
        "series": result.series,
        "retrieved_at": result.retrieved_at,
        "provenance_sha256": result.provenance_sha256,
        "payload": result.payload,
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
