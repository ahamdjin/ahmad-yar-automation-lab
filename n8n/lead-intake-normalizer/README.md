# Lead Intake Normalizer

Normalize inconsistent inbound lead payloads into one predictable JSON shape before sending them to a CRM, notification system, database, or downstream automation.

## Why this exists

Forms and lead sources rarely agree on field names. One source may send `full_name`, another `name`, and another `fullName`. Normalizing early keeps later workflow logic simpler.

## Trigger

`POST /lead-intake-normalizer`

The Webhook node responds through the final Respond to Webhook node.

## Accepted fields

The workflow recognizes common aliases for name, email, phone, company, website, service interest, message, source, UTM attribution, and referrer.

Unknown fields are not copied into the normalized lead object. Their names are listed in `meta.originalKeys` for debugging.

## Setup

1. Import `workflow.json` into n8n.
2. Open the Webhook node and use its test URL.
3. POST `sample-request.json`.
4. Confirm the normalized response.
5. Add CRM/database/notification nodes after **Normalize Lead**, or adapt the response step.
6. Review privacy and retention requirements before sending real lead data.

## Behavior and limitations

- Email addresses are trimmed and lowercased.
- Phone formatting removes spaces and punctuation while preserving a leading `+`.
- Empty strings become `null`.
- The workflow does not validate whether contact details or URLs are genuine.
- The workflow does not deduplicate leads.
- It intentionally contains no credentials or external service calls.

For production use, add schema validation, consent handling, idempotency, and downstream error handling appropriate to your stack.
