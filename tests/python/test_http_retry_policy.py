import unittest
from datetime import datetime, timezone

from gpt_tools.http_retry_policy import decide_retry, parse_retry_after


class HttpRetryPolicyTests(unittest.TestCase):
    def test_retries_safe_method(self):
        result = decide_retry(429, method="GET", attempt=2)
        self.assertTrue(result.retry)
        self.assertEqual(result.delay_seconds, 4.0)

    def test_does_not_retry_post_without_idempotency(self):
        result = decide_retry(503, method="POST")
        self.assertFalse(result.retry)
        self.assertEqual(result.reason, "operation_not_known_idempotent")

    def test_retry_after_seconds(self):
        result = decide_retry(429, method="POST", idempotent=True, retry_after="12")
        self.assertEqual(result.delay_seconds, 12.0)
        self.assertEqual(result.reason, "retry_after")

    def test_retry_after_date(self):
        now = datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        seconds = parse_retry_after("Thu, 01 Jan 2026 00:00:10 GMT", now=now)
        self.assertEqual(seconds, 10.0)


if __name__ == "__main__":
    unittest.main()
