import unittest

from gpt_tools.html_text_extractor import extract_document


class HtmlTextExtractorTests(unittest.TestCase):
    def test_extracts_readable_text_and_links(self):
        html = """
        <html><head><title> Example Page </title><style>.x{}</style></head>
        <body><main><h1>Hello</h1><p>World <a href="/docs">Docs</a></p>
        <script>hiddenNoise()</script></main></body></html>
        """
        doc = extract_document(html, base_url="https://example.com/base")
        self.assertEqual(doc["title"], "Example Page")
        self.assertIn("Hello", doc["text"])
        self.assertIn("World", doc["text"])
        self.assertNotIn("hiddenNoise", doc["text"])
        self.assertEqual(doc["links"], [{"url": "https://example.com/docs"}])


if __name__ == "__main__":
    unittest.main()
