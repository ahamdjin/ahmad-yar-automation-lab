import unittest

from gpt_tools.url_safety_guard import evaluate_url


class UrlSafetyGuardTests(unittest.TestCase):
    def test_allows_public_https(self):
        result = evaluate_url("https://example.com/path?q=1")
        self.assertTrue(result.allowed)
        self.assertEqual(result.normalized_url, "https://example.com/path?q=1")

    def test_rejects_localhost_and_private_ip(self):
        self.assertFalse(evaluate_url("https://localhost/test").allowed)
        self.assertFalse(evaluate_url("https://127.0.0.1/test").allowed)
        self.assertFalse(evaluate_url("https://10.0.0.5/test").allowed)

    def test_rejects_embedded_credentials(self):
        result = evaluate_url("https://user:pass@example.com/data")
        self.assertFalse(result.allowed)
        self.assertEqual(result.reason, "embedded_credentials_not_allowed")

    def test_http_requires_opt_in(self):
        self.assertFalse(evaluate_url("http://example.com").allowed)
        self.assertTrue(evaluate_url("http://example.com", allow_http=True).allowed)


if __name__ == "__main__":
    unittest.main()
