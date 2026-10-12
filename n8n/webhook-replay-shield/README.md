# Webhook Replay Shield

**What it solves:** webhook providers often redeliver events after a timeout or temporary failure. Without a stable ID, a single lead, payment notification or order can trigger repeated downstream work.

This n8n workflow separates **first-seen**, **repeat**, and **invalid** webhook requests. It uses n8n's persisted **Remove Duplicates: Remove Items Processed in Previous Executions** history, so it requires no external database for this introductory pattern. It makes **no CRM changes, emails, charges or external API calls**.

**Important:** this is a best-effort replay filter. It is **not** transactional exactly-once processing. See [idempotency design notes](../../docs/webhook-replay-and-idempotency.md) before connecting irreversible side effects.

## Trigger and request

POST JSON to your n8n instance's Webhook path `webhook-replay-shield`.

```json
{
  "event_id": "evt_demo_20261013_001",
  "source": "crm",
  "event_type": "lead.created",
  "lead": { "name": "Fictional Person", "email": "nobody@example.invalid" }
}
```

Required: `event_id` (alias `eventId`) is a **sender-stable** string of 6–128 ASCII letters, numbers, dots, underscores, colons or hyphens, starting with an alphanumeric character. `source` (alias `origin`) is a 2–40-character ASCII system name, normalized to lowercase; it must begin with a letter and can contain letters, digits, periods, underscores and hyphens. IDs are case-sensitive.

The source must **reuse the exact same ID for retries**. A newly generated ID for each delivery defeats deduplication. Do **not** use names, email addresses, or other personal data as event IDs. The key is `source:event_id`; this separates identical IDs from different senders.

The workflow accepts extra fields but **drops them** from its validated output and responses, so downstream actions only receive the source and event identity. It also rejects bodies with more than 30 top-level fields.

## Response contract

| Condition | Status | Body status |
| --- | ---: | --- |
| First-seen ID | `202 Accepted` | `accepted`, `first_seen` |
| Previously seen ID, same source | `200 OK` | `duplicate_ignored`, `seen_before` |
| Malformed ID/source | `422 Unprocessable Entity` | `rejected`, `invalid_event_envelope` |

Examples: `sample-request.json`, `sample-response.json`, `sample-duplicate-response.json`, `sample-invalid-request.json`, and `sample-invalid-response.json`.

## Import and test

1. Import `workflow.json` into a compatible n8n instance (n8n **1.64+**; uses Remove Duplicates node version 2). It is **inactive** by default.
2. For a safe test, open **Receive Event**, click **Listen for test event**, and send the fictional `sample-request.json` to the generated test webhook URL. Keep the sender and ID unchanged between retries.
3. Re-run the same request in a **separate execution**. It should go to the **Discarded** output of **Remember Seen Event Keys** and return HTTP 200. n8n's test history behavior can vary by version; confirm across published executions too.
4. Send `sample-invalid-request.json`. It should return HTTP 422 and bypass the deduplication node.
5. Before publishing: configure authentication and access control on **Receive Event**, review the history size and execution-data retention settings, and test again using a protected production endpoint.

```bash
curl -sS -i -X POST "$N8N_TEST_WEBHOOK_URL" \
  -H "Content-Type: application/json" \
  --data-binary @sample-request.json
```

**Where to add actions:** place CRM upserts, email/Slack notifications or other operations on the **Kept / first** branch between **Remember Seen Event Keys** and **First Delivery Response**. The **Discarded / second** branch deliberately suppresses repeated event IDs. Never attach side-effect actions to the discarded branch.

## Important security and correctness limits

- **Authentication required before activation.** No credential is shipped. An unauthenticated production webhook is publicly callable and may let an attacker pre-seed event IDs; configure n8n Webhook authentication (for example Header Auth) and, where appropriate, provider-specific signature verification.
- **History is bounded.** The Remove Duplicates node defaults to retaining a finite number of keys (n8n documents 10,000 items). Old IDs can reappear after eviction or resetting the node history.
- **A suppressed retry can hide a failed action.** The key is remembered *before* downstream effects are known to have succeeded. If a CRM write fails, the event may be marked seen and its retry discarded. Use a proper durable state machine (`pending`, `succeeded`, `failed`) for production and allow safe reprocessing after failure.
- **Concurrent deliveries can race.** This workflow does not provide a database-level uniqueness constraint or atomic locking. For money movements, billing, provisioning, and irreversible actions, enforce idempotency with unique event IDs in a durable system and preferably in the target service.
- **n8n may retain request bodies in execution logs.** Filtering the response is not sufficient to protect personal data; configure retention, permissions and sensitive-data handling at the n8n instance level.
- This checks *delivery identity*, not whether two different event IDs refer to the same lead or customer.
- Workflow is intentionally **non-integrated**: no CRM or Slack action is silently activated on import.

## Source references

- [n8n Remove Duplicates](https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.removeduplicates/)
- [n8n Remove Duplicates examples](https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.removeduplicates/templates-and-examples/)
- [n8n Webhook node](https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.webhook/)
- [Webhook production checklist](../../docs/webhook-production-checklist.md)

Maintained by [Ahmad Yar](https://www.ahmadyar.co/) · [Automation Lab](https://github.com/ahamdjin/ahmad-yar-automation-lab)
