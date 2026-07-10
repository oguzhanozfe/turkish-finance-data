import unittest

from turkish_finance_data.portfolio_import import parse_portfolio_export


class PortfolioImportTest(unittest.TestCase):
    def test_normalizes_turkish_allocation_export(self):
        body = (
            "FON KODU;DÖNEM;VARLIK TÜRÜ;ORAN\n"
            "PPF;30.06.2026;Ters Repo;55,5\n"
            "PPF;30.06.2026;Takasbank Para Piyasası;44,5\n"
        ).encode("utf-8")
        rows = parse_portfolio_export(body)
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["fund_code"], "PPF")
        self.assertEqual(rows[0]["report_date"], "2026-06-30")
        self.assertEqual(sum(row["weight_pct"] for row in rows), 100)

    def test_rejects_incomplete_allocation(self):
        body = (
            "fund_code,report_date,asset_class,weight_pct\n"
            "PPF,2026-06-30,Reverse Repo,80\n"
        ).encode()
        with self.assertRaisesRegex(ValueError, "100%"):
            parse_portfolio_export(body)


if __name__ == "__main__":
    unittest.main()
