"""Exact normalized-text deduplication for retrieval JSONL datasets."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import unicodedata
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(frozen=True)
class DedupeStats:
    read: int
    kept: int
    duplicates: int
    invalid: int


def normalize_text(value: str, *, case_sensitive: bool = False) -> str:
    text = unicodedata.normalize("NFKC", value)
    text = " ".join(text.split())
    return text if case_sensitive else text.casefold()


def dedupe_jsonl(
    input_path: str,
    output_path: str,
    *,
    key: str = "text",
    case_sensitive: bool = False,
    keep_invalid: bool = False,
) -> DedupeStats:
    seen: set[str] = set()
    read = kept = duplicates = invalid = 0

    with Path(input_path).open("r", encoding="utf-8") as source, Path(output_path).open("w", encoding="utf-8") as target:
        for line in source:
            if not line.strip():
                continue

            read += 1
            try:
                item = json.loads(line)
            except json.JSONDecodeError:
                invalid += 1
                if keep_invalid:
                    target.write(line if line.endswith("\n") else line + "\n")
                    kept += 1
                continue

            value = item.get(key) if isinstance(item, dict) else None
            if not isinstance(value, str):
                invalid += 1
                if keep_invalid:
                    target.write(json.dumps(item, ensure_ascii=False) + "\n")
                    kept += 1
                continue

            normalized = normalize_text(value, case_sensitive=case_sensitive)
            digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
            if digest in seen:
                duplicates += 1
                continue
            seen.add(digest)

            if "normalized_sha256" not in item:
                item["normalized_sha256"] = digest
            target.write(json.dumps(item, ensure_ascii=False) + "\n")
            kept += 1

    return DedupeStats(read, kept, duplicates, invalid)


def main() -> int:
    parser = argparse.ArgumentParser(description="Deduplicate JSONL retrieval records by normalized text.")
    parser.add_argument("input")
    parser.add_argument("-o", "--output", required=True)
    parser.add_argument("--key", default="text")
    parser.add_argument("--case-sensitive", action="store_true")
    parser.add_argument("--keep-invalid", action="store_true")
    parser.add_argument("--report", action="store_true")
    args = parser.parse_args()

    stats = dedupe_jsonl(
        args.input,
        args.output,
        key=args.key,
        case_sensitive=args.case_sensitive,
        keep_invalid=args.keep_invalid,
    )
    if args.report:
        print(json.dumps(asdict(stats), sort_keys=True), file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
