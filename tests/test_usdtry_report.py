import unittest
from datetime import date

from turkish_finance_data.usdtry_report import calculate_metrics, parse_observations, render_report


class UsdTryReportTest(unittest.TestCase):
    def test_parses_evds_rows_and_ignores_nulls(self):
        payload = {"items": [
            {"Tarih": "01-01-2026", "TP_DK_USD_A": None},
            {"Tarih": "02-01-2026", "TP_DK_USD_A": "42.8457"},
            {"Tarih": "05-01-2026", "TP_DK_USD_A": "43,0000"},
        ]}
        self.assertEqual(parse_observations(payload), [
            (date(2026, 1, 2), 42.8457),
            (date(2026, 1, 5), 43.0),
        ])

    def test_metrics_and_report_have_exactly_30_lines(self):
        observations = [
            (date(2026, 1, 2), 42.8457),
            (date(2026, 4, 1), 44.5000),
            (date(2026, 7, 10), 46.7854),
        ]
        metrics = calculate_metrics(observations)
        self.assertAlmostEqual(metrics.ytd_change, 0.091951, places=5)
        self.assertGreater(metrics.trend_year_end, metrics.last_value)
        report = render_report(metrics)
        self.assertEqual(len(report.splitlines()), 30)
        self.assertTrue(report.splitlines()[0].startswith("01."))
        self.assertTrue(report.splitlines()[-1].startswith("30."))


if __name__ == "__main__":
    unittest.main()
