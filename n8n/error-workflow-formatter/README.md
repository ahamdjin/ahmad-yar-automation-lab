# Error Workflow Formatter

A credential-free starter error workflow for n8n.

It receives an n8n error event, extracts the operationally useful fields, and outputs a compact alert payload that can feed Slack, email, Teams, a ticketing system, or an incident API.

## Why this exists

Raw failure objects are noisy and notification channels should not depend on every detail of n8n's execution payload. Formatting once gives downstream alert steps a smaller, more stable interface.

## Flow

```text
Error Trigger
  -> Format Error Context
  -> add your notification destination
```

## Output

The formatter returns:

- workflow ID and name;
- execution ID, URL, mode, and last node;
- error name, message, and description;
- a human-readable `summary`;
- `alert.title` and `alert.text` fields ready for notification nodes.

## Setup

1. Import `workflow.json`.
2. Add the notification destination you use after **Format Error Context**.
3. In the workflow you want to monitor, choose this workflow as its error workflow in Workflow Settings.
4. Trigger a real automatic failure in a safe test workflow and verify the alert.

n8n's Error Trigger is designed for error workflows and automatic workflow failures. Manual execution behavior is different, so do not treat a manual editor run as the only test.

## Privacy

Do not blindly append the full incoming execution payload to notifications. It may contain customer data or secrets from failed nodes.

This formatter deliberately keeps the output small.

See [../../docs/error-workflows.md](../../docs/error-workflows.md).
