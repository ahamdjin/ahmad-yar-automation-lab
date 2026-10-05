import unittest
from pathlib import Path

from gpt_tools.retrieval_chunker import build_records, chunk_text


class RetrievalChunkerTests(unittest.TestCase):
    def test_chunk_text_respects_limit(self):
        text = ("Alpha " * 80) + "\n\n" + ("Beta " * 80)
        chunks = chunk_text(text, max_chars=300, overlap_chars=40)
        self.assertGreater(len(chunks), 1)
        self.assertTrue(all(len(chunk) <= 300 for chunk in chunks))

    def test_records_have_stable_ids(self):
        path = Path("notes.md")
        chunks = ["one", "two"]
        first = list(build_records(path, chunks))
        second = list(build_records(path, chunks))
        self.assertEqual([r["id"] for r in first], [r["id"] for r in second])
        self.assertEqual(first[0]["source"], "notes.md")


if __name__ == "__main__":
    unittest.main()
