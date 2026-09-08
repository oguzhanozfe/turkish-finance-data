import unittest
from datetime import date

from turkish_finance_data.research_snapshot import analyze_document, analyze_series, render_html


class ResearchSnapshotTests(unittest.TestCase):
    def test_metrics_capture_change_volatility_and_drawdown(self):
        metrics = analyze_series({
            "name": "Example",
            "color": "#ffffff",
            "points": [["2026-01-01", 100], ["2026-02-01", 120], ["2026-03-01", 90]],
        })
        self.assertEqual(metrics.points[0][0], date(2026, 1, 1))
        self.assertAlmostEqual(metrics.change_pct, -10)
        self.assertAlmostEqual(metrics.max_drawdown_pct, -25)
        self.assertGreater(metrics.annualized_volatility_pct, 0)

    def test_document_requires_explicit_provenance_boundary(self):
        with self.assertRaisesRegex(ValueError, "provenance"):
            analyze_document({"series": []})

    def test_html_marks_synthetic_input_and_has_no_external_assets(self):
        document = {
            "title": "Demo",
            "as_of": "2026-06-30",
            "provenance": {"kind": "synthetic", "note": "Synthetic demo."},
            "series": [{
                "name": "Index", "color": "#35dbd2",
                "points": [["2026-01-01", 100], ["2026-02-01", 101]],
            }],
        }
        output = render_html(document, analyze_document(document))
        self.assertIn("Synthetic demo.", output)
        self.assertIn("not investment advice", output)
        self.assertNotIn("<script", output)
        self.assertNotIn("https://", output)


if __name__ == "__main__":
    unittest.main()
