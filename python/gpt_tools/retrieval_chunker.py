"""Paragraph-aware document chunking for retrieval and knowledge pipelines."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from pathlib import Path
from typing import Iterable, Iterator

SUPPORTED_EXTENSIONS = {".txt", ".md", ".json", ".csv"}


def _read_text(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".json":
        data = json.loads(path.read_text(encoding="utf-8"))
        return json.dumps(data, ensure_ascii=False, indent=2)
    if suffix == ".csv":
        rows = []
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.reader(handle)
            for row in reader:
                rows.append(" | ".join(cell.strip() for cell in row))
        return "\n".join(rows)
    return path.read_text(encoding="utf-8")


def discover_files(inputs: Iterable[str]) -> list[Path]:
    found: list[Path] = []
    for raw in inputs:
        path = Path(raw)
        if path.is_dir():
            found.extend(
                candidate for candidate in path.rglob("*")
                if candidate.is_file() and candidate.suffix.lower() in SUPPORTED_EXTENSIONS
            )
        elif path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS:
            found.append(path)
        else:
            raise FileNotFoundError(f"Unsupported or missing input: {path}")
    return sorted(set(found), key=lambda p: str(p).lower())


def _split_long_block(block: str, max_chars: int) -> list[str]:
    block = block.strip()
    if len(block) <= max_chars:
        return [block] if block else []

    pieces: list[str] = []
    cursor = 0
    while cursor < len(block):
        end = min(cursor + max_chars, len(block))
        if end < len(block):
            window = block[cursor:end]
            boundary = max(window.rfind(". "), window.rfind("? "), window.rfind("! "), window.rfind(" "))
            if boundary >= max_chars // 2:
                end = cursor + boundary + 1
        piece = block[cursor:end].strip()
        if piece:
            pieces.append(piece)
        cursor = max(end, cursor + 1)
    return pieces


def _overlap_tail(text: str, overlap_chars: int) -> str:
    if overlap_chars <= 0:
        return ""
    tail = text[-overlap_chars:]
    if len(text) > overlap_chars:
        first_space = tail.find(" ")
        if 0 <= first_space < len(tail) // 3:
            tail = tail[first_space + 1 :]
    return tail.strip()


def chunk_text(text: str, max_chars: int = 4000, overlap_chars: int = 400) -> list[str]:
    if max_chars < 200:
        raise ValueError("max_chars must be at least 200")
    if overlap_chars < 0 or overlap_chars >= max_chars:
        raise ValueError("overlap_chars must be >= 0 and smaller than max_chars")

    normalized = text.replace("\r\n", "\n").replace("\r", "\n").strip()
    if not normalized:
        return []

    blocks: list[str] = []
    for paragraph in [part.strip() for part in re.split(r"\n\s*\n+", normalized) if part.strip()]:
        blocks.extend(_split_long_block(paragraph, max_chars))

    chunks: list[str] = []
    current = ""
    for block in blocks:
        candidate = block if not current else f"{current}\n\n{block}"
        if len(candidate) <= max_chars:
            current = candidate
            continue

        if current:
            chunks.append(current.strip())
            overlap = _overlap_tail(current, overlap_chars)
            current = f"{overlap}\n\n{block}".strip() if overlap else block
        else:
            current = block

        while len(current) > max_chars:
            head = current[:max_chars].rstrip()
            chunks.append(head)
            overlap = _overlap_tail(head, overlap_chars)
            remaining = current[max_chars:].lstrip()
            current = f"{overlap}\n\n{remaining}".strip() if overlap else remaining

    if current.strip():
        chunks.append(current.strip())

    if len(chunks) >= 2 and chunks[-1] and chunks[-1] in chunks[-2]:
        chunks.pop()
    return chunks


def build_records(path: Path, chunks: list[str], base: Path | None = None) -> Iterator[dict]:
    source = str(path.relative_to(base)) if base and path.is_relative_to(base) else str(path)
    for index, text in enumerate(chunks):
        digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
        stable = hashlib.sha256(f"{source}:{index}:{digest}".encode("utf-8")).hexdigest()[:20]
        yield {
            "id": stable,
            "source": source,
            "chunk_index": index,
            "chars": len(text),
            "sha256": digest,
            "text": text,
        }


def run(inputs: list[str], output: str, max_chars: int, overlap_chars: int) -> int:
    paths = discover_files(inputs)
    if not paths:
        raise ValueError("No supported files found")

    base = Path.cwd()
    written = 0
    with Path(output).open("w", encoding="utf-8") as handle:
        for path in paths:
            for record in build_records(path, chunk_text(_read_text(path), max_chars, overlap_chars), base):
                handle.write(json.dumps(record, ensure_ascii=False) + "\n")
                written += 1
    return written


def main() -> int:
    parser = argparse.ArgumentParser(description="Create retrieval-friendly JSONL chunks from text-forward files.")
    parser.add_argument("inputs", nargs="+", help="Files or directories (.txt, .md, .json, .csv)")
    parser.add_argument("-o", "--output", required=True, help="Output JSONL path")
    parser.add_argument("--max-chars", type=int, default=4000)
    parser.add_argument("--overlap-chars", type=int, default=400)
    args = parser.parse_args()
    count = run(args.inputs, args.output, args.max_chars, args.overlap_chars)
    print(f"Wrote {count} chunks to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
