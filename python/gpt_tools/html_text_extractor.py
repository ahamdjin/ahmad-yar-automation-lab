"""Extract compact model-friendly text and links from HTML without external dependencies."""

from __future__ import annotations

import argparse
import json
import re
import sys
from html.parser import HTMLParser
from urllib.parse import urljoin

BLOCK_TAGS = {
    "article", "aside", "blockquote", "br", "dd", "div", "dl", "dt", "figcaption",
    "figure", "footer", "h1", "h2", "h3", "h4", "h5", "h6", "header", "hr", "li",
    "main", "nav", "ol", "p", "pre", "section", "table", "td", "th", "tr", "ul",
}
SKIP_TAGS = {"script", "style", "noscript", "svg", "template"}


class ReadableHtmlParser(HTMLParser):
    def __init__(self, base_url: str | None = None) -> None:
        super().__init__(convert_charrefs=True)
        self.base_url = base_url
        self._skip_depth = 0
        self._title_depth = 0
        self._text_parts: list[str] = []
        self._title_parts: list[str] = []
        self.links: list[dict[str, str]] = []

    def handle_starttag(self, tag: str, attrs) -> None:
        tag = tag.lower()
        if tag in SKIP_TAGS:
            self._skip_depth += 1
            return
        if self._skip_depth:
            return
        if tag == "title":
            self._title_depth += 1
        if tag in BLOCK_TAGS:
            self._text_parts.append("\n")
        if tag == "a":
            href = dict(attrs).get("href")
            if href and not href.lower().startswith(("javascript:", "data:", "mailto:", "tel:")):
                absolute = urljoin(self.base_url, href) if self.base_url else href
                self.links.append({"url": absolute})

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag in SKIP_TAGS and self._skip_depth:
            self._skip_depth -= 1
            return
        if self._skip_depth:
            return
        if tag == "title" and self._title_depth:
            self._title_depth -= 1
        if tag in BLOCK_TAGS:
            self._text_parts.append("\n")

    def handle_data(self, data: str) -> None:
        if self._skip_depth:
            return
        if self._title_depth:
            self._title_parts.append(data)
        self._text_parts.append(data)


def _clean_text(parts: list[str]) -> str:
    raw = "".join(parts).replace("\r", "")
    lines = []
    for line in raw.split("\n"):
        cleaned = re.sub(r"[ \t\f\v]+", " ", line).strip()
        if cleaned:
            lines.append(cleaned)
    return "\n".join(lines)


def extract_document(html: str, *, base_url: str | None = None) -> dict:
    parser = ReadableHtmlParser(base_url=base_url)
    parser.feed(html)
    parser.close()

    unique_links = []
    seen = set()
    for item in parser.links:
        url = item["url"]
        if url not in seen:
            seen.add(url)
            unique_links.append(item)

    return {
        "title": re.sub(r"\s+", " ", " ".join(parser._title_parts)).strip() or None,
        "text": _clean_text(parser._text_parts),
        "links": unique_links,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Extract readable text from HTML for model/retrieval pipelines.")
    parser.add_argument("input", nargs="?", help="HTML file; omit to read stdin")
    parser.add_argument("-o", "--output")
    parser.add_argument("--base-url", help="Base URL used to resolve relative links")
    parser.add_argument("--json", action="store_true", help="Output title/text/links as JSON")
    args = parser.parse_args()

    html = open(args.input, "r", encoding="utf-8").read() if args.input else sys.stdin.read()
    document = extract_document(html, base_url=args.base_url)
    rendered = json.dumps(document, ensure_ascii=False, indent=2) + "\n" if args.json else document["text"] + "\n"

    if args.output:
        with open(args.output, "w", encoding="utf-8") as handle:
            handle.write(rendered)
    else:
        sys.stdout.write(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
