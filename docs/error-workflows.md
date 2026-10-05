# Error Workflow Pattern

n8n can run a dedicated error workflow when another workflow fails. The error workflow starts with the **Error Trigger** node and receives details about the failed workflow/execution.

Official references:

- https://docs.n8n.io/build/flow-logic/handle-errors-gracefully/
- https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.errortrigger/

## Recommended pattern

```text
Error Trigger
  -> Format Error Context
  -> Notification / incident destination
```

The [Error Workflow Formatter](../n8n/error-workflow-formatter/) in this repository handles the middle step. It turns n8n's failure event into a smaller payload with:

- workflow ID and name;
- execution ID and URL;
- last node executed;
- error name and message;
- a human-readable summary;
- a preformatted alert title and text.

That output can then feed Slack, email, Teams, a ticketing system, or an incident API.

## Why format first?

Sending the raw error object directly to a notification channel often produces noisy alerts and couples the notification step to n8n's full execution payload. A formatting step gives downstream channels a stable interface and makes later changes easier.

## Production notes

- Assign the error workflow in the target workflow's settings.
- Error Trigger behavior is for automatic workflow failures; manual testing is different.
- Avoid forwarding secrets or entire input payloads into alerts.
- Include the execution URL when operators have access to the n8n instance.
- Decide which failures need immediate alerts and which can be reviewed asynchronously.
