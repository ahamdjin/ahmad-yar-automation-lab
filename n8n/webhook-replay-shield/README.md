# Webhook Replay Shield

**What it solves:** webhook providers often redeliver events after a timeout or temporary failure. Without a stable ID, a single lead, payment notification or order can trigger repeated downstream work.

This n8n workflow accepts **first-seen** webhook IDs, silently filters **repeat** deliveries, and explicitly rejects **invalid** requests. It uses n8n's persisted **Remove Duplicates: Remove Items Processed in Previous Executions** history, so it requires no external database for this introductory pattern. It makes **no CRM changes, emails, charges or external API calls**.

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
| Previously seen ID, same source | `200 OK` (n8n's standard fallback) | No custom JSON body; the Remove Duplicates node emits no item |
| Malformed ID/source | `422 Unprocessable Entity` | `rejected`, `invalid_event_envelope` |

Examples: `sample-request.json`, `sample-response.json`, `sample-invalid-request.json`, and `sample-invalid-response.json`. There is **no JSON `duplicate_ignored` response** in this version. A repeated event is filtered out, and n8n returns its documented standard HTTP 200 message because no Respond to Webhook node is reached.

## Import and test

1. Import `workflow.json` into a compatible n8n instance (n8n **1.64+**; uses Remove Duplicates node version 2). It is **inactive** by default.
2. For a safe test, open **Receive Event**, click **Listen for test event**, and send the fictional `sample-request.json` to the generated test webhook URL. Keep the sender and ID unchanged between retries.
3. Send the same request in a **separate execution**. The Remove Duplicates node should show the ID in its **Discarded** result, with **no item flowing downstream**. n8n returns its **standard HTTP 200** response (not a custom JSON reply). Test-mode history behavior can vary; confirm using a protected, published workflow as well.
4. Send `sample-invalid-request.json`. It should return HTTP 422 and bypass the deduplication node.
5. Before publishing: configure authentication and access control on **Receive Event**, review the history size and execution-data retention settings, and test again using a protected production endpoint.

```bash
curl -sS -i -X POST "$N8N_TEST_WEBHOOK_URL" \
  -H "Content-Type: application/json" \
  --data-binary @sample-request.json
```

**Where to add actions:** connect CRM upserts, email/Slack notifications or other actions **after Remember Seen Event Keys**, in the one **main/Kept** output path, before **First Delivery Response**. Duplicate events are **discarded inside the node**, not routed through a second canvas output. Do **not** draw a connection from a nonexistent second port.

**Using this in an existing workflow:** you need **one webhook**, not two. Copy the normalization/validation logic (or map your existing stable ID to `eventKey`) followed by **Remember Seen Event Keys** into your original workflow, and connect its single outgoing path to your existing business nodes. This standalone demo intentionally removes additional customer fields after validation; when adapting to CRM work, keep the necessary source fields in your flow, and verify permission and PII retention settings.

## Important security and correctness limits

- **Authentication required before activation.** No credential is shipped. An unauthenticated production webhook is publicly callable and may let an attacker pre-seed event IDs; configure n8n Webhook authentication (for example Header Auth) and, where appropriate, provider-specific signature verification.
- **Where the ID lives:** n8n saves the deduplication key in its own persisted processed-item history, scoped to this node. It is **not held for only a few seconds** or stored in the browser. This example explicitly configures a 10,000-entry history size (a count limit, **not a TTL**). Retention, eviction and full-history behavior vary by n8n version; old IDs may be accepted again after reset/eviction, and some older versions can error on a full history. Check node execution data and the history-size option before production.
- **A suppressed retry can hide a failed action.** The key is remembered *before* downstream effects are known to have succeeded. If a CRM write fails, the event may be marked seen and its retry discarded. Use a proper durable state machine (`pending`, `succeeded`, `failed`) for production and allow safe reprocessing after failure.
- **Concurrent deliveries can race.** This workflow does not provide a database-level uniqueness constraint or atomic locking. For money movements, billing, provisioning, and irreversible actions, enforce idempotency with unique event IDs in a durable system and preferably in the target service.
- **n8n may retain request bodies in execution logs.** Filtering the response is not sufficient to protect personal data; configure retention, permissions and sensitive-data handling at the n8n instance level.
- This checks *delivery identity*, not whether two different event IDs refer to the same lead or customer.
- Workflow is intentionally **non-integrated**: no CRM or Slack action is silently activated on import.

## Source references

- [n8n Remove Duplicates](https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.removeduplicates/)
- [n8n Remove Duplicates examples](https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.removeduplicates/templates-and-examples/)
- [n8n Webhook node](https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.webhook/)
- [n8n Respond to Webhook: the standard HTTP 200 fallback when no response node runs](https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.respondtowebhook/)
- [Webhook production checklist](../../docs/webhook-production-checklist.md)

Maintained by [Ahmad Yar](https://www.ahmadyar.co/) · [Automation Lab](https://github.com/ahamdjin/ahmad-yar-automation-lab)
