"""Unified CLI for gpt_tools."""

from __future__ import annotations

import argparse
import sys

from . import openapi_action_auditor, pii_redactor, retrieval_chunker, tool_output_compactor


def main() -> int:
    parser = argparse.ArgumentParser(prog="gpt-tools")
    parser.add_argument("command", choices=["chunk", "redact", "compact", "audit-action"])
    args, rest = parser.parse_known_args()
    sys.argv = [sys.argv[0], *rest]
    return {
        "chunk": retrieval_chunker.main,
        "redact": pii_redactor.main,
        "compact": tool_output_compactor.main,
        "audit-action": openapi_action_auditor.main,
    }[args.command]()


if __name__ == "__main__":
    raise SystemExit(main())
