# Webhook Replay Protection vs. Exactly-Once Processing

Webhooks are commonly delivered at least once. An HTTP timeout doesn't tell the sender whether the receiver did something, so a provider may redeliver. Protect your operations by using stable event IDs, deliberate responses, and destination-side uniqueness.

## Which level of protection do you need?

| Level | Technique | Protection | Caveat |
| --- | --- | --- | --- |
| Demo | In-memory array inside one execution | Repeats in that execution | No protection across executions |
| Starter | n8n Remove Duplicates / previous executions | Previously seen event keys | Bounded history; not transaction-safe |
| Production | Durable idempotency table with unique `(source,event_id)` | Cross-worker unique reservation | Requires recovery and expiration policies |
| Highest integrity | Durable reservation + exactly-once business state via unique external ID and transactional outbox | Prevents repeating supported operations even across crashes | Depends on target storage/side effects and careful architecture |

## Recommended state machine

1. Normalize and validate a signed or authenticated source event. Compute a stable source-scoped idempotency key.
2. Atomically insert the unique key into a database with status `pending`, or load an existing key.
3. If status is `succeeded`, return a cached receipt; if `pending`, return an in-progress receipt or choose a lease/timeout policy.
4. Carry out a retry-safe operation in the destination using that same external event key. Prefer a unique constraint or upsert.
5. Only after the destination confirms success, mark status `succeeded` with a receipt. Save retryable `failed` states separately; retry using bounded backoff.
6. Account for out-of-order event versions, storage retention, dead letters, observability, and the sender's retry policy.

**There is no generic n8n node graph that turns a non-transactional external API into exactly-once delivery.** If the side effect and idempotency state are not in one transaction, failure windows remain.

## Notes on the public Replay Shield example

The example uses n8n's history store on the **first-seen** path, before any real integration. It returns HTTP 202 for keys newly admitted, 200 for duplicate keys, and 422 for invalid envelopes. These codes are deliberately explicit; external webhook senders may interpret non-2xx statuses differently.

Treat it as a **filter or learning example**, not an authoritative success receipt for any business action. Its default history size is finite; a legitimate event may be rediscovered after eviction or history reset. Do not add charging/billing actions directly without a proper durable ledger.

Docs: [Remove Duplicates](https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.removeduplicates/) · [Webhook](https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.webhook/)
