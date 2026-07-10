import unittest

from turkish_finance_data.tefas_import import parse_tefas_export


class TefasImportTest(unittest.TestCase):
    def test_normalizes_user_supplied_csv(self):
        rows = parse_tefas_export(
            b"fund_code,valuation_date,price\ntp2,2026-07-09,2.05\n", "text/csv"
        )
        self.assertEqual(rows[0]["series_code"], "TEFAS:TP2")
        self.assertEqual(rows[0]["value"], 2.05)
        self.assertEqual(len(rows[0]["provenance_sha256"]), 64)

    def test_rejects_zero_price_markers(self):
        with self.assertRaisesRegex(ValueError, "positive"):
            parse_tefas_export(
                b'[{"fund_code":"TP2","valuation_date":"2026-07-09","price":0}]',
                "application/json",
            )


if __name__ == "__main__":
    unittest.main()
