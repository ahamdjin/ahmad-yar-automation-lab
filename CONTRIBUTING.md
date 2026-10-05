# Contributing

This repository favors small, reusable automation patterns over client-specific exports.

## Before you submit

A contribution should solve a clear operational problem, use fictional sample data, contain no credentials or customer data, use descriptive node names, remain inactive in the committed export, and include documentation for setup, input, output, assumptions, and failure modes.

## Workflow folder convention

```text
n8n/
  workflow-slug/
    README.md
    workflow.json
    sample-request.json
    sample-response.json
```

Use kebab-case for folder names. Keep one primary workflow per folder.

## Validation

```bash
npm run validate
```

## Pull requests

Explain the problem, expected input/output, required services or credentials, how you tested it, and any production risks or limitations.

By contributing, you agree that your contribution is licensed under the repository's MIT License.
