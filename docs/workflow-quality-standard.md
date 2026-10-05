# Workflow Quality Standard

A public automation workflow should be understandable, safe to inspect, and straightforward to adapt.

## 1. Clear purpose

The folder README must explain the business problem in plain language.

## 2. Predictable interface

Document the trigger type, expected fields, optional fields, output shape, and status/error behavior. When practical, include fictional sample request and response files.

## 3. Safe defaults

Public exports should be inactive. They should not send email, create records, delete data, charge cards, or call private endpoints immediately after import without an explicit setup step.

## 4. Credential hygiene

Never include secret values. Minimize exported credential metadata and document required credentials separately.

## 5. Observable logic

Prefer descriptive node names and explicit rules. If a Code node contains business logic, keep it readable and document the rule set.

## 6. Failure modes

Document what happens when required input is missing, an API is unavailable, or a downstream service returns an unexpected response.

## 7. Portability

Avoid hardcoded client IDs, internal URLs, proprietary field names, or assumptions that only make sense in one account.

## 8. Production review

Before activation, review authentication, rate limits, retries, idempotency, data retention, privacy, and failure handling for the target system.
