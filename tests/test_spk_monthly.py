import unittest

from turkish_finance_data.spk_monthly import (
    OLE_XLS_SIGNATURE,
    SpkMonthlyClient,
    extract_aggregate_sheet,
)


class FakeSheet:
    def __init__(self, rows):
        self.rows = rows
        self.nrows = len(rows)

    def cell_value(self, row, column):
        return self.rows[row][column] if column < len(self.rows[row]) else ""


class FakeResponse:
    def __init__(self, body, url):
        self.body = body
        self.url = url

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False

    def read(self, _limit):
        return self.body

    def geturl(self):
        return self.url


class SpkMonthlyTest(unittest.TestCase):
    def test_extracts_aggregate_fund_row(self):
        sheet = FakeSheet([
            ["Yıl", "Ay", "Fon Sayısı"],
            [2025.0, "08", 1868.0, 6334406.733, 6608768.0,
             10.08, 5.89, 21.07, 1.17, 22.06, 3.76, 26.58, 3.3, 4.24, 1.84],
            [2025.0, "(*) 09", "moved to Takasbank"],
        ])
        rows = extract_aggregate_sheet(sheet, "mutual_funds", "III-1-5")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["period"], "2025-08")
        self.assertEqual(rows[0]["fund_count"], 1868)
        self.assertEqual(rows[0]["allocations"]["term_deposit_pct"], 26.58)

    def test_fetches_only_spk_legacy_xls(self):
        url = "https://spk.gov.tr/data/example/monthly.xls"
        body = OLE_XLS_SIGNATURE + b"workbook"
        captured = {}

        def opener(request, timeout):
            captured["url"] = request.full_url
            captured["timeout"] = timeout
            return FakeResponse(body, url)

        result = SpkMonthlyClient(opener).fetch(url)
        self.assertEqual(captured["url"], url)
        self.assertEqual(result.body, body)
        self.assertEqual(len(result.provenance_sha256), 64)

    def test_rejects_non_spk_url(self):
        with self.assertRaisesRegex(ValueError, "spk.gov.tr"):
            SpkMonthlyClient().fetch("https://example.com/monthly.xls")


if __name__ == "__main__":
    unittest.main()
