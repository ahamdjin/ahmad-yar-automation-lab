"""Conservative PII and secret redaction before text reaches a model or log."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from dataclasses import dataclass


@dataclass(frozen=True)
class RedactionResult:
    text: str
    counts: dict[str, int]


SECRET_PATTERNS = [
    re.compile(r"(?i)\b(authorization)\s*:\s*(bearer\s+)[A-Za-z0-9._~+/=-]{8,}"),
    re.compile(r"(?i)\b(api[_-]?key|access[_-]?token|refresh[_-]?token|password|client[_-]?secret)\b(\s*[:=]\s*)[\"']?([^\s,\"'}]{6,})"),
    re.compile(r"\bghp_[A-Za-z0-9]{20,}\b"),
    re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}\b"),
    re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{20,}\b"),
    re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
]
EMAIL_RE = re.compile(r"(?<![\w.+-])[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}(?![\w.-])")
IPV4_RE = re.compile(r"(?<!\d)(?:(?:25[0-5]|2[0-4]\d|1?\d?\d)\.){3}(?:25[0-5]|2[0-4]\d|1?\d?\d)(?!\d)")
PHONE_RE = re.compile(r"(?<!\w)(?:\+?\d[\d().\s-]{7,}\d)(?!\w)")
CARD_CANDIDATE_RE = re.compile(r"(?<!\d)(?:\d[ -]?){12,18}\d(?!\d)")


def _luhn(value: str) -> bool:
    digits = [int(c) for c in value if c.isdigit()]
    if not 13 <= len(digits) <= 19:
        return False
    total = 0
    parity = len(digits) % 2
    for index, digit in enumerate(digits):
        if index % 2 == parity:
            digit *= 2
            if digit > 9:
                digit -= 9
        total += digit
    return total % 10 == 0


def redact_text(text: str) -> RedactionResult:
    counts: Counter[str] = Counter()
    counters: Counter[str] = Counter()

    def placeholder(kind: str) -> str:
        counters[kind] += 1
        counts[kind] += 1
        return f"[{kind}_{counters[kind]}]"

    def secret_sub(match: re.Match[str]) -> str:
        if match.lastindex and match.lastindex >= 3:
            return f"{match.group(1)}{match.group(2)}{placeholder('SECRET')}"
        if match.lastindex and match.lastindex >= 2:
            return f"{match.group(1)}: {match.group(2)}{placeholder('SECRET')}"
        return placeholder("SECRET")

    redacted = text
    for pattern in SECRET_PATTERNS:
        redacted = pattern.sub(secret_sub, redacted)

    redacted = EMAIL_RE.sub(lambda _: placeholder("EMAIL"), redacted)

    def card_sub(match: re.Match[str]) -> str:
        return placeholder("CARD") if _luhn(match.group(0)) else match.group(0)

    redacted = CARD_CANDIDATE_RE.sub(card_sub, redacted)
    redacted = IPV4_RE.sub(lambda _: placeholder("IP"), redacted)

    def phone_sub(match: re.Match[str]) -> str:
        candidate = match.group(0)
        digits = re.sub(r"\D", "", candidate)
        if 10 <= len(digits) <= 15:
            return placeholder("PHONE")
        return candidate

    redacted = PHONE_RE.sub(phone_sub, redacted)
    return RedactionResult(redacted, dict(counts))


def main() -> int:
    parser = argparse.ArgumentParser(description="Redact common PII/secrets from text.")
    parser.add_argument("input", nargs="?", help="Input text file; omit to read stdin")
    parser.add_argument("-o", "--output", help="Output file; omit to write stdout")
    parser.add_argument("--report", action="store_true", help="Write redaction counts to stderr")
    args = parser.parse_args()

    text = open(args.input, "r", encoding="utf-8").read() if args.input else sys.stdin.read()
    result = redact_text(text)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as handle:
            handle.write(result.text)
    else:
        sys.stdout.write(result.text)

    if args.report:
        sys.stderr.write(json.dumps(result.counts, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
