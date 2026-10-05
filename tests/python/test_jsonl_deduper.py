import json
import tempfile
import unittest
from pathlib import Path

from gpt_tools.jsonl_deduper import dedupe_jsonl, normalize_text


class JsonlDeduperTests(unittest.TestCase):
    def test_normalization(self):
        self.assertEqual(normalize_text("  Hello   WORLD "), "hello world")

    def test_dedupes_normalized_text(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "input.jsonl"
            target = Path(directory) / "output.jsonl"
            rows = [
                {"id": 1, "text": "Hello   world"},
                {"id": 2, "text": " hello world "},
                {"id": 3, "text": "Different"},
            ]
            source.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")
            stats = dedupe_jsonl(str(source), str(target))
            output = [json.loads(line) for line in target.read_text(encoding="utf-8").splitlines()]
            self.assertEqual(stats.duplicates, 1)
            self.assertEqual(len(output), 2)
            self.assertIn("normalized_sha256", output[0])


if __name__ == "__main__":
    unittest.main()
