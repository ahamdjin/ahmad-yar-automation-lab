# Webhook Payload Validator

Validate a simple contact/lead payload before it reaches a CRM, database, notification system, or AI workflow.

## Why this exists

Webhook integrations often fail later than they should. A missing email address or malformed field reaches downstream systems, which makes errors harder to understand and can create partial records.

This workflow moves basic validation to the boundary.

## Trigger

`POST /webhook-payload-validator`

## Default rules

- `name` is required.
- `email` is required.
- `email` must have a basic email shape.
- `message` may be omitted but must be 2000 characters or fewer when present.
- common aliases such as `full_name` and `email_address` are accepted.

## Responses

Valid payloads return HTTP `200`.

Invalid payloads return HTTP `422` with an `errors` array describing the rejected fields.

## Setup

1. Import `workflow.json`.
2. Use the Webhook node's test URL.
3. POST `sample-request.json`.
4. Change the required fields and limits inside **Validate Payload** to match your real form/API contract.
5. Add downstream actions only after validation.
6. Add webhook authentication if the caller supports it.

## Production considerations

This example performs practical boundary validation, not full security validation.

For production systems, consider schema validation, authentication/signature verification, rate limiting at the edge, idempotency, consent requirements, and field-specific constraints.

See [../../docs/webhook-production-checklist.md](../../docs/webhook-production-checklist.md).
