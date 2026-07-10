import json
import unittest

from turkish_finance_data.evds import EvdsClient


class FakeResponse:
    def __init__(self, value, content_type="application/json"):
        self.body = value if isinstance(value, bytes) else json.dumps(value).encode()
        self.headers = {"Content-Type": content_type}

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False

    def read(self):
        return self.body

    def geturl(self):
        return "https://evds3.tcmb.gov.tr/igmevdsms-dis/test"


class EvdsClientTest(unittest.TestCase):
    def test_key_is_a_header_and_provenance_is_returned(self):
        captured = {}

        def opener(request, timeout):
            captured["request"] = request
            captured["timeout"] = timeout
            return FakeResponse({"items": [{"Tarih": "01-07-2026"}]})

        result = EvdsClient("secret-key", opener).fetch(
            ["TP.EXAMPLE.SERIES"], "01-07-2026", "10-07-2026"
        )
        self.assertNotIn("secret-key", captured["request"].full_url)
        self.assertIn("/igmevdsms-dis/series=", captured["request"].full_url)
        self.assertEqual(captured["request"].get_header("Key"), "secret-key")
        self.assertEqual(result.series, ["TP.EXAMPLE.SERIES"])
        self.assertEqual(len(result.provenance_sha256), 64)

    def test_rejects_bad_dates_before_request(self):
        with self.assertRaisesRegex(ValueError, "DD-MM-YYYY"):
            EvdsClient("key").fetch(["TP.TEST"], "2026-07-01", "10-07-2026")

    def test_explains_html_service_redirect(self):
        def opener(_request, timeout):
            return FakeResponse(b"<html>EVDS application</html>", "text/html")

        with self.assertRaisesRegex(Exception, "HTML instead of JSON"):
            EvdsClient("key", opener).fetch(["TP.TEST"], "01-07-2026", "10-07-2026")


if __name__ == "__main__":
    unittest.main()
