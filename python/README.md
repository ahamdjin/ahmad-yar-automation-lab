# Python GPT / Agent Toolkit

Dependency-light utilities for the unglamorous parts of production GPT and agent systems: preparing retrieval data, reducing unsafe context, shrinking tool payloads, and checking action schemas before deployment.

These utilities are intentionally useful outside one OpenAI surface. They can sit around current GPT Actions, Responses/API tool loops, plugin-style integrations, n8n automations, or other model runtimes.

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

OpenAI's current GPT Actions configuration uses an OpenAPI schema to tell ChatGPT which server to call, which operations exist, and what parameters they accept. This auditor does not replace the GPT editor's own validation.

## Unified CLI

You can also run:

```bash
PYTHONPATH=python python -m gpt_tools chunk ...
PYTHONPATH=python python -m gpt_tools redact ...
PYTHONPATH=python python -m gpt_tools compact ...
PYTHONPATH=python python -m gpt_tools audit-action ...
```

## Testing

```bash
PYTHONPATH=python python -m unittest discover -s tests/python -p 'test_*.py'
```

The repository CI runs these tests alongside the n8n workflow validator.

## Maintainer

Built and maintained by [Ahmad Yar](https://www.ahmadyar.co/) as part of the Ahmad Yar Automation Lab.

The public scripts here are generic building blocks. Client credentials, private infrastructure, production customer data, and proprietary implementations are intentionally excluded.
