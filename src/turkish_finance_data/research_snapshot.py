import argparse
import html
import json
import math
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from statistics import stdev
from typing import Any, Dict, List, Optional, Sequence, Tuple


@dataclass(frozen=True)
class SeriesMetrics:
    name: str
    color: str
    points: Tuple[Tuple[date, float], ...]
    change_pct: float
    annualized_volatility_pct: float
    max_drawdown_pct: float


def analyze_series(series: Dict[str, Any], periods_per_year: int = 12) -> SeriesMetrics:
    name = str(series.get("name", "")).strip()
    color = str(series.get("color", "#35dbd2")).strip()
    raw_points = series.get("points")
    if not name or not isinstance(raw_points, list) or len(raw_points) < 2:
        raise ValueError("each named series needs at least two points")

    points: List[Tuple[date, float]] = []
    for raw in raw_points:
        if not isinstance(raw, list) or len(raw) != 2:
            raise ValueError("points must be [YYYY-MM-DD, value] pairs")
        observed = date.fromisoformat(str(raw[0]))
        value = float(raw[1])
        if not math.isfinite(value) or value <= 0:
            raise ValueError("series values must be finite and positive")
        points.append((observed, value))
    if points != sorted(points, key=lambda item: item[0]) or len({p[0] for p in points}) != len(points):
        raise ValueError("series dates must be unique and ascending")

    returns = [math.log(points[index][1] / points[index - 1][1]) for index in range(1, len(points))]
    volatility = stdev(returns) * math.sqrt(periods_per_year) * 100 if len(returns) > 1 else 0.0
    peak = points[0][1]
    drawdown = 0.0
    for _, value in points:
        peak = max(peak, value)
        drawdown = min(drawdown, value / peak - 1)

    return SeriesMetrics(
        name=name,
        color=color,
        points=tuple(points),
        change_pct=(points[-1][1] / points[0][1] - 1) * 100,
        annualized_volatility_pct=volatility,
        max_drawdown_pct=drawdown * 100,
    )


def analyze_document(document: Dict[str, Any]) -> List[SeriesMetrics]:
    if document.get("provenance", {}).get("kind") not in {"synthetic", "attributed-derived"}:
        raise ValueError("provenance.kind must be synthetic or attributed-derived")
    series = document.get("series")
    if not isinstance(series, list) or not series:
        raise ValueError("document needs a non-empty series list")
    return [analyze_series(item) for item in series]


def _chart(metrics: Sequence[SeriesMetrics], width: int = 920, height: int = 330) -> str:
    left, top, right, bottom = 70, 34, 24, 54
    chart_width = width - left - right
    chart_height = height - top - bottom
    normalized = [[value / item.points[0][1] * 100 for _, value in item.points] for item in metrics]
    values = [value for row in normalized for value in row]
    low = math.floor(min(values) - 2)
    high = math.ceil(max(values) + 2)
    span = max(1, high - low)

    parts = [f'<svg viewBox="0 0 {width} {height}" role="img" aria-label="Indexed synthetic series chart">']
    for index in range(5):
        y = top + chart_height * index / 4
        value = high - span * index / 4
        parts.append(f'<line x1="{left}" y1="{y:.1f}" x2="{width-right}" y2="{y:.1f}" stroke="#273654"/>')
        parts.append(f'<text x="{left-12}" y="{y+5:.1f}" text-anchor="end" fill="#8191b2" font-size="13">{value:.0f}</text>')
    for item, values_for_series in zip(metrics, normalized):
        denominator = max(1, len(values_for_series) - 1)
        coordinates = []
        for index, value in enumerate(values_for_series):
            x = left + chart_width * index / denominator
            y = top + (high - value) / span * chart_height
            coordinates.append(f"{x:.1f},{y:.1f}")
        parts.append(f'<polyline points="{" ".join(coordinates)}" fill="none" stroke="{html.escape(item.color)}" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/>')
        for coordinate in coordinates:
            x, y = coordinate.split(",")
            parts.append(f'<circle cx="{x}" cy="{y}" r="5" fill="{html.escape(item.color)}" stroke="#07101f" stroke-width="3"/>')
    labels = metrics[0].points
    for index, (observed, _) in enumerate(labels):
        x = left + chart_width * index / max(1, len(labels) - 1)
        parts.append(f'<text x="{x:.1f}" y="{height-18}" text-anchor="middle" fill="#8191b2" font-size="12">{observed:%b}</text>')
    parts.append("</svg>")
    return "".join(parts)


def render_html(document: Dict[str, Any], metrics: Sequence[SeriesMetrics]) -> str:
    title = html.escape(str(document.get("title", "Research snapshot")))
    as_of = html.escape(str(document.get("as_of", "")))
    provenance = html.escape(str(document.get("provenance", {}).get("note", "")))
    cards = "".join(
        f'<article class="card"><span style="background:{html.escape(item.color)}"></span>'
        f'<h2>{html.escape(item.name)}</h2><strong>{item.change_pct:+.1f}%</strong>'
        f'<dl><div><dt>Annualized volatility</dt><dd>{item.annualized_volatility_pct:.1f}%</dd></div>'
        f'<div><dt>Max drawdown</dt><dd>{item.max_drawdown_pct:.1f}%</dd></div></dl></article>'
        for item in metrics
    )
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title><style>
:root{{--bg:#07101f;--surface:#111b32;--raised:#192645;--text:#f6f8ff;--muted:#92a2c3}}
*{{box-sizing:border-box}} body{{margin:0;background:var(--bg);color:var(--text);font:16px/1.5 system-ui,sans-serif}}
main{{max-width:1080px;margin:auto;padding:64px 32px}} .eyebrow{{color:#35dbd2;font-weight:750;letter-spacing:.1em;font-size:13px}}
h1{{font-size:clamp(36px,6vw,62px);line-height:1;margin:.2em 0}} .intro{{color:var(--muted);max-width:680px}}
.chart{{background:var(--surface);border:1px solid #273654;margin:38px 0 20px;padding:18px;border-radius:18px}}
.cards{{display:grid;grid-template-columns:repeat(3,1fr);gap:14px}} .card{{background:var(--raised);padding:22px;border-radius:16px}}
.card span{{display:block;width:30px;height:5px;border-radius:9px}} h2{{font-size:15px;color:var(--muted)}} strong{{font-size:32px}}
dl div{{display:flex;justify-content:space-between;gap:12px}} dt{{color:var(--muted)}} dd{{margin:0}} footer{{color:var(--muted);margin-top:28px;font-size:14px}}
@media(max-width:760px){{main{{padding:36px 18px}}.cards{{grid-template-columns:1fr}}}}
</style></head><body><main><div class="eyebrow">OFFLINE RESEARCH OUTPUT · {as_of}</div><h1>{title}</h1>
<p class="intro">A reproducible comparison view generated by the toolkit. Values are normalized to 100 at the first observation.</p>
<section class="chart">{_chart(metrics)}</section><section class="cards">{cards}</section>
<footer>{provenance} This output is not investment advice.</footer></main></body></html>'''


def render_readme_svg(document: Dict[str, Any], metrics: Sequence[SeriesMetrics]) -> str:
    title = html.escape(str(document.get("title", "Research snapshot")))
    chart = _chart(metrics, 920, 300)
    legend = "".join(
        f'<circle cx="{62 + index * 285}" cy="558" r="6" fill="{html.escape(item.color)}"/>'
        f'<text x="{76 + index * 285}" y="563" fill="#dfe6f7" font-size="15">{html.escape(item.name)}  {item.change_pct:+.1f}%</text>'
        for index, item in enumerate(metrics)
    )
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1040" height="620" viewBox="0 0 1040 620">
<rect width="1040" height="620" rx="26" fill="#07101f"/><text x="58" y="68" fill="#35dbd2" font-family="system-ui" font-size="14" font-weight="700" letter-spacing="2">REPRODUCIBLE RESEARCH OUTPUT</text>
<text x="58" y="124" fill="#f6f8ff" font-family="system-ui" font-size="38" font-weight="750">{title}</text>
<text x="58" y="158" fill="#92a2c3" font-family="system-ui" font-size="16">Synthetic values · normalized to 100 · no network required</text>
<g transform="translate(58 190)"><rect width="924" height="322" rx="16" fill="#111b32"/>{chart}</g>{legend}</svg>'''


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Build an offline financial research snapshot")
    parser.add_argument("--input", required=True, help="attributed-derived or synthetic JSON series")
    parser.add_argument("--html", required=True, help="output HTML path")
    parser.add_argument("--svg", help="optional README preview path")
    args = parser.parse_args(argv)
    document = json.loads(Path(args.input).read_text(encoding="utf-8"))
    metrics = analyze_document(document)
    html_path = Path(args.html)
    html_path.parent.mkdir(parents=True, exist_ok=True)
    html_path.write_text(render_html(document, metrics), encoding="utf-8")
    if args.svg:
        svg_path = Path(args.svg)
        svg_path.parent.mkdir(parents=True, exist_ok=True)
        svg_path.write_text(render_readme_svg(document, metrics), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

