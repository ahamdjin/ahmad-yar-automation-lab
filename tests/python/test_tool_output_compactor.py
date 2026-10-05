import unittest

from gpt_tools.tool_output_compactor import CompactionStats, compact


class ToolOutputCompactorTests(unittest.TestCase):
    def test_redacts_and_limits(self):
        stats = CompactionStats()
        result = compact(
            {"api_key": "example", "items": list(range(10)), "text": "x" * 50, "empty": None},
            max_string=10,
            max_items=3,
            stats=stats,
        )
        self.assertEqual(result["api_key"], "[REDACTED]")
        self.assertEqual(result["items"][-1], {"_truncated_items": 7})
        self.assertIn("truncated", result["text"])
        self.assertNotIn("empty", result)
        self.assertEqual(stats.redacted_fields, 1)
        self.assertEqual(stats.truncated_lists, 1)

    def test_max_depth(self):
        stats = CompactionStats()
        result = compact({"a": {"b": {"c": 1}}}, max_depth=2, stats=stats)
        self.assertEqual(result["a"]["b"], "[MAX_DEPTH_REACHED]")
        self.assertEqual(stats.max_depth_hits, 1)


if __name__ == "__main__":
    unittest.main()
