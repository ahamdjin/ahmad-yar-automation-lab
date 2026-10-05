"""Compact large tool/API JSON payloads before returning them to a model."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass

DEFAULT_SENSITIVE_KEYS = {
    "password", "passwd", "secret", "client_secret", "api_key", "apikey",
    "access_token", "refresh_token", "authorization", "cookie", "set-cookie",
    "x-api-key", "private_key",
}


@dataclass
class CompactionStats:
    truncated_strings: int = 0
    truncated_lists: int = 0
    max_depth_hits: int = 0
    redacted_fields: int = 0
    dropped_nulls: int = 0


def _is_sensitive(key: str) -> bool:
    normalized = key.lower().replace("-", "_")
    normalized_defaults = {item.replace("-", "_") for item in DEFAULT_SENSITIVE_KEYS}
    return normalized in normalized_defaults or normalized.endswith("_token") or normalized.endswith("_secret")


def compact(
    value,
    *,
    max_string: int = 1200,
    max_items: int = 25,
    max_depth: int = 8,
    drop_nulls: bool = True,
    stats: CompactionStats | None = None,
    _depth: int = 0,
):
    stats = stats or CompactionStats()
    if _depth >= max_depth and isinstance(value, (dict, list)):
        stats.max_depth_hits += 1
        return "[MAX_DEPTH_REACHED]"

    if isinstance(value, dict):
        output = {}
        for key, child in value.items():
            if drop_nulls and child is None:
                stats.dropped_nulls += 1
                continue
            if _is_sensitive(str(key)):
                output[key] = "[REDACTED]"
                stats.redacted_fields += 1
            else:
                output[key] = compact(
                    child, max_string=max_string, max_items=max_items, max_depth=max_depth,
                    drop_nulls=drop_nulls, stats=stats, _depth=_depth + 1,
                )
        return output

    if isinstance(value, list):
        output = [
            compact(
                child, max_string=max_string, max_items=max_items, max_depth=max_depth,
                drop_nulls=drop_nulls, stats=stats, _depth=_depth + 1,
            )
            for child in value[:max_items]
        ]
        if len(value) > max_items:
            output.append({"_truncated_items": len(value) - max_items})
            stats.truncated_lists += 1
        return output

    if isinstance(value, str) and len(value) > max_string:
        removed = len(value) - max_string
        stats.truncated_strings += 1
        return value[:max_string].rstrip() + f"…[truncated {removed} chars]"

    return value


def main() -> int:
    parser = argparse.ArgumentParser(description="Compact and redact JSON tool output for model context.")
    parser.add_argument("input", nargs="?", help="Input JSON file; omit to read stdin")
    parser.add_argument("-o", "--output", help="Output JSON file; omit to write stdout")
    parser.add_argument("--max-string", type=int, default=1200)
    parser.add_argument("--max-items", type=int, default=25)
    parser.add_argument("--max-depth", type=int, default=8)
    parser.add_argument("--keep-nulls", action="store_true")
    parser.add_argument("--stats", action="store_true", help="Write compaction stats to stderr")
    args = parser.parse_args()

    raw = open(args.input, "r", encoding="utf-8").read() if args.input else sys.stdin.read()
    data = json.loads(raw)
    stats = CompactionStats()
    result = compact(
        data, max_string=args.max_string, max_items=args.max_items, max_depth=args.max_depth,
        drop_nulls=not args.keep_nulls, stats=stats,
    )
    rendered = json.dumps(result, ensure_ascii=False, indent=2) + "\n"

    if args.output:
        with open(args.output, "w", encoding="utf-8") as handle:
            handle.write(rendered)
    else:
        sys.stdout.write(rendered)

    if args.stats:
        sys.stderr.write(json.dumps(stats.__dict__, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
