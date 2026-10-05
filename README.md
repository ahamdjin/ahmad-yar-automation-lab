# Ahmad Yar Automation Lab

Production-minded automation workflows, n8n patterns, integration utilities, and practical examples for real business systems.

This repository is a public working library: each asset should solve a specific problem, explain its assumptions, avoid embedded secrets, and be useful beyond a single client implementation.

## What lives here

| Area | Purpose |
| --- | --- |
| `n8n/` | Importable n8n workflows with setup notes and sample payloads |
| `snippets/` | Reusable JavaScript helpers for automation work |
| `docs/` | Architecture notes, conventions, and implementation guides |
| `scripts/` | Repository tooling and validation utilities |

## Workflow catalog

| Workflow | What it does | Credentials required |
| --- | --- | --- |
| [Lead Intake Normalizer](n8n/lead-intake-normalizer/) | Accepts inconsistent lead payloads and returns a predictable schema | No |
| [Local Business Lead Router](n8n/local-business-lead-router/) | Scores and routes inbound leads using explicit, editable rules | No |

More workflows will be added as they are documented and generalized enough to be safely reused.

## Principles

- **Useful before impressive.** Every workflow should solve a real operational problem.
- **Portable by default.** Public assets should not depend on private client infrastructure.
- **No secrets in exports.** Credentials, tokens, personal data, and internal URLs do not belong in this repository.
- **Explain the tradeoffs.** READMEs should document inputs, outputs, assumptions, and failure modes.
- **Human-readable automation.** Node names, code, and routing rules should make the workflow understandable without reverse engineering it.
- **Safe examples.** Sample payloads use fictional data and placeholder domains.

## Quick start

1. Open the README inside the workflow folder.
2. Import its `workflow.json` into n8n.
3. Review every node and replace placeholder configuration where documented.
4. Use n8n's test URL before activating a webhook workflow.
5. Send a sample payload and verify the output before connecting production systems.

## Validation

Workflow exports are validated in CI for JSON syntax, required top-level workflow fields, duplicate node names, broken connection targets, duplicate webhook paths, sibling documentation, and common secret patterns.

Run the same check locally:

```bash
npm run validate
```

## Contributing

Contributions are welcome when they improve a reusable automation pattern rather than expose a one-off private implementation. See [CONTRIBUTING.md](CONTRIBUTING.md) and the [workflow quality standard](docs/workflow-quality-standard.md) before opening a pull request.

## Security

Never commit credentials or real customer data. If you discover a security issue, follow [SECURITY.md](SECURITY.md).

## Maintainer

Maintained by [Ahmad Yar](https://www.ahmadyar.co/) — automation systems, AI workflows, integrations, and backend infrastructure.

## License

MIT — see [LICENSE](LICENSE).
