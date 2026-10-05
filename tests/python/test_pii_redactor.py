import unittest

from gpt_tools.pii_redactor import redact_text


class PiiRedactorTests(unittest.TestCase):
    def test_redacts_common_values(self):
        text = "Email jordan@example.com phone +1 (555) 010-2020 from 192.168.1.5"
        result = redact_text(text)
        self.assertNotIn("jordan@example.com", result.text)
        self.assertNotIn("555", result.text)
        self.assertNotIn("192.168.1.5", result.text)
        self.assertEqual(result.counts["EMAIL"], 1)
        self.assertEqual(result.counts["PHONE"], 1)
        self.assertEqual(result.counts["IP"], 1)

    def test_luhn_cards_only(self):
        result = redact_text("valid 4242 4242 4242 4242 invalid 1234 5678 9012 3456")
        self.assertIn("[CARD_1]", result.text)
        self.assertIn("1234 5678 9012 3456", result.text)

    def test_redacts_named_secret_field(self):
        result = redact_text("api_key=example_placeholder_value")
        self.assertIn("api_key=[SECRET_1]", result.text)
        self.assertNotIn("example_placeholder_value", result.text)


if __name__ == "__main__":
    unittest.main()
