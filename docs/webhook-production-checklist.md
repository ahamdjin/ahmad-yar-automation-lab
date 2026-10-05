# Webhook Production Checklist

Use this checklist before moving an imported webhook workflow from testing into production.

n8n provides separate test and production webhook URLs. Build and debug with the test URL, then publish the workflow before relying on its production URL.

Official references:

- https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.webhook/
- https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.webhook/workflow-development/
- https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.respondtowebhook/

## Request boundary

- Decide which HTTP methods are allowed.
- Require authentication when the caller supports it.
- Validate required fields before creating records or triggering side effects.
- Set practical field-size limits.
- Treat headers, query parameters, and request bodies as untrusted input.
- If signature verification requires the raw request body, enable and preserve it before transforming data.

## Response behavior

- Choose the response mode intentionally.
- For request/response API patterns, use a Respond to Webhook node.
- Set the HTTP status code explicitly.
- Return 4xx responses for caller/input problems and 5xx responses for server/downstream failures where appropriate.
- Do not return a 200 success response with an error-shaped body.

## Reliability

- Add idempotency when providers may retry the same event.
- Decide what happens if a downstream CRM, database, or API is slow or unavailable.
- Configure retries only for operations that are safe to retry.
- Avoid creating duplicate contacts, bookings, invoices, or notifications.
- Use an error workflow for failures that require operational attention.

## Data handling

- Collect only the fields you need.
- Do not log secrets or unnecessary personal data.
- Understand where execution data is retained.
- Remove real customer data before sharing workflow exports.

## Go-live

- Test with the n8n test webhook first.
- Test invalid payloads, not only the happy path.
- Test downstream failure behavior.
- Publish the workflow.
- Switch the caller to the production webhook URL.
- Confirm one real production request end to end.
- Monitor early executions for unexpected payloads or retries.
