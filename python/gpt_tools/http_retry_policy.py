"""Deterministic retry decisions for HTTP-based GPT/agent tools."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

RETRYABLE_STATUS = {408, 425, 429, 500, 502, 503, 504}
IDEMPOTENT_METHODS = {"GET", "HEAD", "OPTIONS", "PUT", "DELETE"}


@dataclass(frozen=True)
class RetryDecision:
    retry: bool
    delay_seconds: float | None
    reason: str


def parse_retry_after(value: str | None, *, now: datetime | None = None) -> float | None:
    if not value:
        return None
    value = value.strip()
    if value.isdigit():
        return max(0.0, float(value))

    try:
        when = parsedate_to_datetime(value)
    except (TypeError, ValueError, OverflowError):
        return None

    if when.tzinfo is None:
        when = when.replace(tzinfo=timezone.utc)
    now = now or datetime.now(timezone.utc)
    return max(0.0, (when - now).total_seconds())


def decide_retry(
    status: int,
    *,
    method: str = "GET",
    attempt: int = 0,
    retry_after: str | None = None,
    idempotent: bool = False,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
) -> RetryDecision:
    method = method.upper()
    safe_to_repeat = idempotent or method in IDEMPOTENT_METHODS

    if status not in RETRYABLE_STATUS:
        return RetryDecision(False, None, "status_not_retryable")

    if not safe_to_repeat:
        return RetryDecision(False, None, "operation_not_known_idempotent")

    explicit = parse_retry_after(retry_after)
    if explicit is not None:
        return RetryDecision(True, min(explicit, max_delay), "retry_after")

    delay = min(base_delay * (2 ** max(0, attempt)), max_delay)
    return RetryDecision(True, delay, "exponential_backoff")


def main() -> int:
    parser = argparse.ArgumentParser(description="Decide whether an HTTP tool call should be retried.")
    parser.add_argument("status", type=int)
    parser.add_argument("--method", default="GET")
    parser.add_argument("--attempt", type=int, default=0)
    parser.add_argument("--retry-after")
    parser.add_argument("--idempotent", action="store_true", help="Explicitly mark the operation safe to repeat")
    parser.add_argument("--base-delay", type=float, default=1.0)
    parser.add_argument("--max-delay", type=float, default=60.0)
    args = parser.parse_args()

    decision = decide_retry(
        args.status,
        method=args.method,
        attempt=args.attempt,
        retry_after=args.retry_after,
        idempotent=args.idempotent,
        base_delay=args.base_delay,
        max_delay=args.max_delay,
    )
    print(json.dumps(asdict(decision), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
