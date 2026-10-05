# Ahmad Yar Automation Lab

[![Validate automation library](https://github.com/ahamdjin/ahmad-yar-automation-lab/actions/workflows/validate.yml/badge.svg)](https://github.com/ahamdjin/ahmad-yar-automation-lab/actions/workflows/validate.yml)

Reusable n8n workflows, Python utilities, automation patterns, and implementation notes for real business systems.

The goal is simple: publish small automation building blocks that are safe to inspect, easy to adapt, and useful before you connect them to a CRM, help desk, database, messaging platform, or AI layer.

## Start here

| Workflow | Use it when you need to... | Credentials |
| --- | --- | --- |
| [Lead Intake Normalizer](n8n/lead-intake-normalizer/) | turn inconsistent lead forms into one predictable schema | None |
| [Local Business Lead Router](n8n/local-business-lead-router/) | score and route inbound service-business leads with transparent rules | None |
| [Webhook Payload Validator](n8n/webhook-payload-validator/) | reject malformed contact payloads before they reach downstream systems | None |
| [UTM Attribution Normalizer](n8n/utm-attribution-normalizer/) | standardize campaign attribution and strip tracking parameters from landing URLs | None |
| [Error Workflow Formatter](n8n/error-workflow-formatter/) | turn n8n failure events into a clean alert payload for Slack, email, or incident tools | None |

## Python toolkit for GPT / agent systems

| Utility | Use it when you need to... |
| --- | --- |
| [Retrieval Chunker](python/README.md#1-retrieval-chunker) | turn Markdown, text, JSON, or CSV into deterministic retrieval JSONL |
| [PII + Secret Redactor](python/README.md#2-pii--secret-redactor) | remove common sensitive values before model context or logs |
| [Tool-output Compactor](python/README.md#3-tool-output-compactor) | shrink large API/tool responses and redact secret-bearing fields |
| [OpenAPI Action Auditor](python/README.md#4-openapi-action-auditor) | catch common GPT/action schema problems before deployment |
| [URL Safety Guard](python/README.md#5-url-safety-guard) | reject localhost/private/unsafe model-selected URLs before server-side fetches |
| [HTML Text Extractor](python/README.md#6-html-text-extractor) | turn noisy HTML into compact text and normalized links |
| [HTTP Retry Policy](python/README.md#7-http-retry-policy) | retry transient API failures without blindly repeating unsafe operations |
| [JSONL Retrieval Deduper](python/README.md#8-jsonl-retrieval-deduper) | remove normalized duplicate chunks before retrieval/indexing |

The Python package uses only the standard library for its core tools. See [python/README.md](python/README.md) for installation, examples, limitations, and production caveats.

## What lives here

| Area | Purpose |
| --- | --- |
| `n8n/` | Importable n8n workflows with setup notes and fictional sample payloads |
| `python/` | Reusable Python utilities for GPT, agent, retrieval, and tool pipelines |
| `snippets/` | Reusable JavaScript helpers for Code nodes and automation scripts |
| `docs/` | Architecture notes, production checklists, and implementation guides |
| `scripts/` | Repository validation tooling |
| `.github/` | CI, issue forms, and contribution templates |

## How to use a workflow

1. Open the workflow folder and read its README first.
2. Import its `workflow.json` into n8n.
3. Use the test webhook URL while developing.
4. Send the included fictional sample payload.
5. Review every rule and assumption before connecting production systems.
6. Add authentication, idempotency, retries, consent handling, and observability where your use case requires them.
7. Publish only after testing the production path.

For webhook-specific production checks, use [docs/webhook-production-checklist.md](docs/webhook-production-checklist.md).

## Quality standard

Every public workflow or utility should:

- solve a specific operational problem;
- contain no secrets or real customer data;
- document inputs, outputs, assumptions, and failure modes;
- include fictional examples where useful;
- make business rules visible instead of hiding them behind vague "AI" labels;
- state clearly what still needs production hardening.

The full n8n standard is in [docs/workflow-quality-standard.md](docs/workflow-quality-standard.md).

## Validation

CI validates n8n workflow structure and runs the Python unit-test suite. It checks workflow JSON, node names and IDs, connection targets, webhook path collisions, explicit webhook response codes, documentation, sample payloads, common secret patterns, and Python behavior.

Run the checks locally:

```bash
npm run validate
PYTHONPATH=python python -m unittest discover -s tests/python -p 'test_*.py'
python -m compileall -q python
```

## n8n references

These patterns follow n8n's documented webhook and error-workflow behavior:

- Webhook node: https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.webhook/
- Webhook development flow: https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.webhook/workflow-development/
- Respond to Webhook: https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.respondtowebhook/
- Error handling: https://docs.n8n.io/build/flow-logic/handle-errors-gracefully/

## Contributing

Useful contributions are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md), [SECURITY.md](SECURITY.md), and [MAINTAINERS.md](MAINTAINERS.md).

## Maintainer

Maintained by [Ahmad Yar](https://www.ahmadyar.co/) — automation systems, AI workflows, integrations, and backend infrastructure.

If you need a reusable example, open an issue. If you need architecture or implementation work for a production system, the maintainer's portfolio has the relevant project context and contact route.

## License

Apache License 2.0 — see [LICENSE](LICENSE).
