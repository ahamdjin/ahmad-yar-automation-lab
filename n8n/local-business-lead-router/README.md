# Local Business Lead Router

Apply transparent lead-priority rules to an inbound request and return a routing decision that can drive CRM assignment, notifications, or follow-up automations.

## Why this exists

Many local businesses need a simple answer before adding AI or complex scoring: **which inquiries need attention first?**

This workflow uses explicit rules that are easy to audit and change.

## Trigger

`POST /local-business-lead-router`

## Default scoring

| Signal | Score |
| --- | ---: |
| Reachable contact: email or phone | +2 |
| Service identified | +2 |
| Urgent language: urgent, emergency, today, same day, ASAP | +3 |
| Commercial intent: quote, estimate, book, appointment, schedule, consult | +2 |

Routing:

- **6+** → `high` → `priority-intake`
- **3–5** → `medium` → `standard-intake`
- **0–2** → `low` → `nurture`

These are example rules, not universal lead-quality truth. Adjust them to the business before production use.

## Setup

1. Import `workflow.json`.
2. Open the Webhook node and use its test URL.
3. POST `sample-request.json`.
4. Confirm the score and route.
5. Edit **Score and Route Lead** to match the business's actual qualification rules.
6. Add CRM assignment, notifications, or follow-up branches after the scoring node.

## Production considerations

- Do not treat this example score as an objective measure of customer value.
- Avoid using protected or sensitive personal traits in lead scoring.
- Add schema validation for required fields.
- Add idempotency if the same lead can be delivered more than once.
- Add retry/error handling before connecting external systems.
- Keep scoring rules understandable to the people operating the business.
