# Python GPT / Agent Toolkit

Dependency-light utilities for the unglamorous parts of production GPT and agent systems: preparing retrieval data, reducing unsafe context, shrinking tool payloads, validating action schemas, guarding model-selected URLs, cleaning HTML, handling transient HTTP failures, and keeping retrieval corpora clean.

These utilities are intentionally useful outside one OpenAI surface. They can sit around GPT Actions, Responses/API tool loops, plugin-style integrations, n8n automations, MCP-backed workflows, or other model runtimes.

## Install

The core package uses only the Python standard library.

```bash
python -m pip install -e .
```

YAML support for the OpenAPI auditor is optional:

```bash
python -m pip install -e '.[yaml]'
```

Python 3.11+ is required.

## 1. Retrieval chunker

Turn text-forward files into deterministic JSONL chunks with source metadata and SHA-256 hashes.

```bash
gpt-chunk ./knowledge ./docs \
  --output chunks.jsonl \
  --max-chars 4000 \
  --overlap-chars 400
```

Supported input: Markdown, text, JSON, and CSV.

Good for:

- preparing retrieval corpora;
- building inspectable knowledge pipelines;
- deduplicating or versioning chunks by hash;
- debugging exactly what context was generated from which source.

The chunker is character-based on purpose. It does not pretend character counts are exact model token counts.

## 2. PII + secret redactor

Remove common sensitive values before text is sent to a model, written to a debug log, or stored in a prompt trace.

```bash
cat support-ticket.txt | gpt-redact --report > support-ticket.redacted.txt
```

It detects common patterns for:

- email addresses;
- phone numbers;
- IPv4 addresses;
- Luhn-valid payment-card candidates;
- common API/token/secret patterns.

This is a safety layer, not a compliance product. Real privacy programs still need data classification, access controls, retention rules, and service-specific review.

## 3. Tool-output compactor

Large API responses are expensive and often distract the model with irrelevant fields. The compactor recursively trims them before they enter model context.

```bash
gpt-compact api-response.json \
  --output compact.json \
  --max-items 20 \
  --max-string 1000 \
  --max-depth 8 \
  --stats
```

Default behavior:

- redacts common secret-bearing keys;
- removes null fields;
- truncates long strings;
- limits long arrays;
- prevents runaway nested data.

Use it between a REST/MCP/function call and the model when the upstream API returns much more data than the model needs.

## 4. OpenAPI action auditor

Review an OpenAPI schema for common problems that make GPT/model actions unreliable.

```bash
gpt-action-audit python/examples/action-openapi.json
```

Checks include:

- OpenAPI 3.x;
- public HTTPS servers;
- stable, unique `operationId` values;
- useful operation/parameter descriptions;
- request schemas;
- documented success responses;
- duplicate/missing action identifiers;
- unauthenticated state-changing endpoints;
- overly broad action surfaces.

JSON works with no dependencies. YAML input requires the optional `yaml` extra.

This auditor does not replace the platform's own schema validation. It is an earlier engineering check for action surfaces that are ambiguous, unsafe, or difficult for a model to call reliably.

## 5. URL safety guard

Check a model-selected URL before a backend fetch.

```bash
gpt-url-check https://example.com/resource
```

By default it:

- allows HTTPS only;
- rejects localhost;
- rejects embedded credentials;
- rejects literal private, loopback, link-local, multicast, reserved, and unspecified IP addresses;
- normalizes IDN hostnames;
- strips fragments before returning the normalized URL.

For server-side tools, add DNS resolution:

```bash
gpt-url-check https://example.com/resource --resolve-dns
```

With `--resolve-dns`, resolved addresses are also rejected if they are non-public.

This reduces common SSRF mistakes but is **not a complete fetch sandbox**. Production fetchers must also validate every redirect target, consider DNS rebinding/TOCTOU risk, apply egress controls, limit response size/time, and restrict protocols in the actual HTTP client.

## 6. HTML text extractor

Strip noisy HTML into compact text that is easier to send into retrieval or model context.

```bash
gpt-html-text python/examples/page.html \
  --base-url https://example.com \
  --json
```

It:

- ignores script, style, noscript, SVG, and template content;
- preserves useful block boundaries;
- extracts the page title;
- extracts and deduplicates links;
- resolves relative links when a base URL is supplied;
- ignores JavaScript/data/mail/tel link schemes.

This is intentionally a parser, not a browser. It does not execute JavaScript, render SPAs, evaluate CSS visibility, or bypass access controls.

## 7. HTTP retry policy

Make retry decisions explicitly instead of blindly retrying every failed tool call.

```bash
gpt-retry 429 --method GET --attempt 2
```

The helper knows common transient HTTP statuses and honors `Retry-After` when provided.

By default it retries only methods that are normally safe to repeat:

- GET
- HEAD
- OPTIONS
- PUT
- DELETE

A POST or PATCH is not retried unless you explicitly mark the operation idempotent:

```bash
gpt-retry 503 --method POST --idempotent
```

The built-in exponential backoff is deterministic so it is easy to test. Distributed production systems should usually add jitter at the caller layer to avoid synchronized retries.

## 8. JSONL retrieval deduper

Remove exact duplicates from retrieval datasets after Unicode/whitespace normalization.

```bash
gpt-dedupe-jsonl python/examples/retrieval-duplicates.jsonl \
  --output deduped.jsonl \
  --report
```

Default behavior:

- Unicode NFKC normalization;
- whitespace collapsing;
- case-insensitive comparison;
- SHA-256 fingerprinting;
- keeps the first occurrence;
- adds `normalized_sha256` to retained records.

Use `--case-sensitive` when casing is meaningful.

This performs exact normalized-text deduplication. It does **not** claim to detect semantically similar paraphrases; semantic dedupe needs embeddings or another similarity system and should be evaluated separately.

## Unified CLI

You can also run every tool through the package:

```bash
PYTHONPATH=python python -m gpt_tools chunk ...
PYTHONPATH=python python -m gpt_tools redact ...
PYTHONPATH=python python -m gpt_tools compact ...
PYTHONPATH=python python -m gpt_tools audit-action ...
PYTHONPATH=python python -m gpt_tools url-check ...
PYTHONPATH=python python -m gpt_tools html-text ...
PYTHONPATH=python python -m gpt_tools retry ...
PYTHONPATH=python python -m gpt_tools dedupe-jsonl ...
```

## Testing

```bash
PYTHONPATH=python python -m unittest discover -s tests/python -p 'test_*.py'
python -m compileall -q python
```

The repository CI runs these tests alongside the n8n workflow validator and CLI smoke tests.

## Maintainer

Built and maintained by [Ahmad Yar](https://www.ahmadyar.co/) as part of the Ahmad Yar Automation Lab.

The public scripts here are generic building blocks. Client credentials, private infrastructure, production customer data, and proprietary implementations are intentionally excluded.
