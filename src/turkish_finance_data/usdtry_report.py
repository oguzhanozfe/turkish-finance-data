import argparse
import math
import os
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from statistics import stdev
from typing import Any, Dict, List, Optional, Sequence, Tuple

from .evds import EvdsClient


SERIES_CODE = "TP.DK.USD.A"


@dataclass(frozen=True)
class FxMetrics:
    first_date: date
    first_value: float
    last_date: date
    last_value: float
    observations: int
    ytd_change: float
    annualized_volatility: float
    max_drawdown: float
    trend_year_end: float


def _number(value: Any) -> Optional[float]:
    if value in (None, "", "null", "NaN"):
        return None
    try:
        return float(str(value).replace(",", "."))
    except ValueError:
        return None


def parse_observations(payload: Dict[str, Any], series_code: str = SERIES_CODE) -> List[Tuple[date, float]]:
    """Extract dated numeric observations without depending on EVDS key casing."""
    expected = series_code.replace(".", "_").upper()
    rows: List[Tuple[date, float]] = []
    for item in payload.get("items", []):
        raw_date = item.get("Tarih") or item.get("DATE") or item.get("Date")
        if not raw_date:
            continue
        parsed_date = None
        for pattern in ("%d-%m-%Y", "%d.%m.%Y", "%Y-%m-%d"):
            try:
                parsed_date = datetime.strptime(str(raw_date), pattern).date()
                break
            except ValueError:
                pass
        if parsed_date is None:
            continue
        raw_value = next(
            (value for key, value in item.items() if key.replace(".", "_").upper() == expected),
            None,
        )
        value = _number(raw_value)
        if value is not None and value > 0:
            rows.append((parsed_date, value))
    return sorted(set(rows))


def calculate_metrics(observations: Sequence[Tuple[date, float]]) -> FxMetrics:
    if len(observations) < 2:
        raise ValueError("at least two numeric USD/TRY observations are required")
    ordered = sorted(observations)
    first_date, first_value = ordered[0]
    last_date, last_value = ordered[-1]
    elapsed = (last_date - first_date).days
    if elapsed <= 0:
        raise ValueError("observations must span more than one calendar day")
    log_returns = [math.log(current[1] / previous[1]) for previous, current in zip(ordered, ordered[1:])]
    volatility = stdev(log_returns) * math.sqrt(252) if len(log_returns) > 1 else 0.0
    peak = ordered[0][1]
    max_drawdown = 0.0
    for _, value in ordered:
        peak = max(peak, value)
        max_drawdown = min(max_drawdown, value / peak - 1)
    year_end = date(last_date.year, 12, 31)
    trend_year_end = last_value * math.exp(
        math.log(last_value / first_value) / elapsed * (year_end - last_date).days
    )
    return FxMetrics(
        first_date=first_date,
        first_value=first_value,
        last_date=last_date,
        last_value=last_value,
        observations=len(ordered),
        ytd_change=last_value / first_value - 1,
        annualized_volatility=volatility,
        max_drawdown=max_drawdown,
        trend_year_end=trend_year_end,
    )


def render_report(metrics: FxMetrics) -> str:
    """Render exactly 30 numbered report lines for the 10 July 2026 snapshot."""
    cpi_ytd = 0.1776
    cpi_annual = 0.3211
    ppi_annual = 0.2809
    policy_rate = 0.37
    expected_12m_cpi = 0.2381
    survey_year_end_usdtry = 51.4692
    real_fx_change = (1 + metrics.ytd_change) / (1 + cpi_ytd) - 1
    ex_ante_real_policy = (1 + policy_rate) / (1 + expected_12m_cpi) - 1
    remaining_to_central = survey_year_end_usdtry / metrics.last_value - 1
    low, central, high = 49.0, 51.5, 56.0
    lines = [
        f"01. Kapsam: {metrics.first_date:%d.%m.%Y}–{metrics.last_date:%d.%m.%Y}; kaynak [TCMB EVDS](https://evds3.tcmb.gov.tr/) `{SERIES_CODE}` ABD doları döviz alış kuru.",
        f"02. İlk iş günü kuru {metrics.first_value:.4f} TL, son gözlem {metrics.last_value:.4f} TL'dir.",
        f"03. Dolar/TL yılbaşından bu yana %{metrics.ytd_change * 100:.2f} yükseldi; başka deyişle TL dolar karşısında yaklaşık %{(1 - metrics.first_value / metrics.last_value) * 100:.2f} değer kaybetti.",
        f"04. Hesap {metrics.observations} geçerli iş günü gözlemine dayanıyor; hafta sonu ve boş EVDS değerleri ileri taşınmadı.",
        f"05. Günlük log getirilerden yıllıklandırılmış oynaklık %{metrics.annualized_volatility * 100:.2f}, dönem içi azami geri çekilme %{abs(metrics.max_drawdown) * 100:.2f} oldu.",
        f"06. [TÜİK Haziran TÜFE](https://veriportali.tuik.gov.tr/tr/press/58289) aylık %0,99, yıllık %{cpi_annual * 100:.2f}, Aralık 2025'e göre %{cpi_ytd * 100:.2f} arttı.",
        f"07. Basit reel karşılaştırmada doların TL getirisi TÜFE'nin yaklaşık %{abs(real_fx_change) * 100:.2f} gerisinde kaldı; bu resmi reel efektif kur hesabı değildir.",
        f"08. Bu fark, 2026'nın ilk yarısında kontrollü nominal kur artışının iç fiyat artışından daha yavaş kaldığını gösteriyor.",
        f"09. [TÜİK Haziran Yİ-ÜFE](https://veriportali.tuik.gov.tr/tr/press/58032) yıllık %{ppi_annual * 100:.2f}, aylık %1,80 arttı; üretici maliyet baskısı sürse de yıllık oran TÜFE'nin altında.",
        f"10. [TCMB 11 Haziran kararı](https://tcmb.gov.tr/wps/wcm/connect/TR/TCMB+TR/Main+Menu/Duyurular/Basin/2026/DUY2026-24): politika faizi %37; gecelik borç verme %40 ve borçlanma %35,5.",
        f"11. Anketteki 12 aylık %{expected_12m_cpi * 100:.2f} enflasyon beklentisine göre geometrik ex-ante reel politika faizi yaklaşık %{ex_ante_real_policy * 100:.2f} pozitiftir.",
        "12. Pozitif reel faiz, TL mevduat ve kısa vadeli TL araçlarının dolara karşı taşıma getirisi üretmesini sağlayan ana savunmadır.",
        "13. Bu savunmanın işlemesi için enflasyon beklentilerinin bozulmaması, faiz indirimlerinin erken olmaması ve kur şokunun sınırlı kalması gerekir.",
        f"14. Sadece Ocak–Temmuz log eğilimini yıl sonuna uzatan mekanik model {metrics.trend_year_end:.2f} TL üretir; model politika veya şok bilmez.",
        f"15. [TCMB Haziran Piyasa Katılımcıları Anketi](https://www.tcmb.gov.tr/wps/wcm/connect/085d78c0-9809-4b33-a6b6-21e0a22a6405/PKA_Rapor.pdf) yıl sonu ortalaması {survey_year_end_usdtry:.4f} TL, 12 ay sonrası 55,7196 TL'dir.",
        f"16. Bizim merkez senaryomuz 51,5 TL'dir; bugünkü seviyeden yıl sonuna yaklaşık %{remaining_to_central * 100:.1f} ek nominal yükseliş demektir.",
        f"17. Tahmin bandımız 49–56 TL'dir; tek nokta yerine bu bandı kullanmak kurun politik ve jeopolitik kuyruk risklerini daha dürüst yansıtır.",
        "18. Güçlü-TL senaryosu 49–50: sıkı faiz, rezerv birikimi, turizm dövizi, düşük enerji faturası ve güvenilir dezenflasyon birlikte gerekir.",
        "19. Merkez senaryo 50,5–52,5: kademeli kur artışı, ihtiyatlı faiz indirimleri ve enflasyonun piyasa beklentisine yaklaşmasını varsayar.",
        "20. Zayıf-TL senaryosu 54–56: enerji/jeopolitik şok, risk primi artışı, sermaye çıkışı veya enflasyondan hızlı faiz indirimiyle oluşabilir.",
        "21. Makro yukarı risk: anketin 2026 cari açık beklentisi 49,2 milyar dolar; dış finansman ihtiyacı TL'yi küresel risk iştahına duyarlı bırakır.",
        "22. Makro destek: anketin %3,2 büyüme beklentisi çok güçlü iç talep yerine dengelenmeyle uyumlu olursa ithalat ve döviz talebi sınırlanabilir.",
        "23. Mikro destek: ihracatçı döviz bozumları ve yaz turizmi piyasaya düzenli döviz arzı sağlayabilir.",
        "24. Mikro risk: ithalatçıların enerji, ara malı ve borç ödemesi için öne çekilmiş dolar talebi kısa süreli sıçramalar yaratabilir.",
        "25. Hanehalkı açısından belirleyici kıyas yalnız dolar/TL değildir; stopaj sonrası net TL getirisi, enflasyon ve likidite birlikte ölçülmelidir.",
        "26. Siyasi gelişmeler kuru doğrudan formülle belirlemez; kurumlara güven, politika öngörülebilirliği, ülke risk primi ve sermaye akımı kanallarından etkiler.",
        "27. İzlenecek haftalık göstergeler: TCMB rezervleri, yabancı menkul kıymet akımları, TL mevduat faizi, kredi büyümesi ve dolarizasyon.",
        "28. İzlenecek aylık göstergeler: TÜFE ana eğilimi, cari denge, dış ticaret, reel efektif kur ve Piyasa Katılımcıları Anketi revizyonları.",
        "29. Tahmin kuralı: enflasyon beklentisi yükselir veya reel faiz tamponu küçülürse bandı yukarı; rezerv/güven güçlenirse aşağı güncelle.",
        "30. Sonuç: baz tahmin 51,5 TL ve makul risk bandı 49–56 TL; bu senaryo analizi kişisel yatırım tavsiyesi veya kesin fiyat vaadi değildir.",
    ]
    if len(lines) != 30:
        raise AssertionError("report must contain exactly 30 lines")
    return "\n".join(lines) + "\n"


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Generate the 30-line 2026 USD/TRY scenario report")
    parser.add_argument("--as-of", default="10-07-2026", help="DD-MM-YYYY")
    parser.add_argument("--output", help="optional Markdown output path")
    args = parser.parse_args(argv)
    as_of = datetime.strptime(args.as_of, "%d-%m-%Y").date()
    if as_of.year != 2026:
        parser.error("this snapshot report currently supports 2026 only")
    key = os.environ.get("EVDS_API_KEY", "")
    if not key:
        parser.error("EVDS_API_KEY is not set")
    response = EvdsClient(key).fetch([SERIES_CODE], "01-01-2026", args.as_of)
    metrics = calculate_metrics(parse_observations(response.payload))
    report = render_report(metrics)
    if args.output:
        path = Path(args.output)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(report, encoding="utf-8")
    else:
        print(report, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
