# Contributing

This repository favors small, reusable automation patterns over client-specific exports.

## General rules

A contribution should:

- solve a clear operational problem;
- use fictional sample data;
- contain no credentials, tokens, private URLs, customer identifiers, or execution history;
- document assumptions and failure modes;
- avoid unnecessary dependencies;
- explain any credential or environment-variable requirements without including values.

## n8n workflow convention

```text
n8n/
  workflow-slug/
    README.md
    workflow.json
    sample-request.json
    sample-response.json
```

Use kebab-case for folder names. Keep one primary workflow per folder.

A public n8n export must use descriptive node names, remain inactive, and document setup, inputs, outputs, and production limitations.

## Python utility convention

Python utilities live in `python/gpt_tools/`.

A new utility should:

- expose useful importable functions instead of hiding all logic in `main()`;
- include a CLI when the task makes sense from a shell or automation runner;
- use the standard library unless an external dependency materially improves the tool;
- accept untrusted input defensively and fail with clear messages;
- avoid network calls by default unless network access is the point of the utility;
- produce deterministic output where practical;
- document what it does **not** guarantee;
- include unit tests under `tests/python/`;
- include a realistic example when the input format is non-obvious.

Optional dependencies should be isolated behind extras and should not be required for the core test suite.

## Validation

Run both validation suites before opening a PR:

```bash
npm run validate
PYTHONPATH=python python -m unittest discover -s tests/python -p 'test_*.py'
python -m compileall -q python
```

## Pull requests

Keep the scope narrow. Explain:

1. the operational problem being solved;
2. expected input and output;
3. required services, credentials, or dependencies;
4. how you tested it;
5. production risks or limitations.

By contributing, you agree that your contribution is licensed under the repository's Apache License 2.0.
