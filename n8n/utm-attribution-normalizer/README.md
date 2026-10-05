# UTM Attribution Normalizer

Turn inconsistent campaign parameters, click IDs, referrer data, and landing URLs into one predictable attribution object.

## Why this exists

Marketing and lead systems often receive the same concepts under slightly different shapes. Cleaning attribution once makes CRM fields, analytics events, reports, and downstream routing more consistent.

## Trigger

`POST /utm-attribution-normalizer`

The workflow reads values from the request body and query object.

## Output

It returns:

- source, medium, campaign, term, and content;
- a simple channel classification;
- Google/Facebook click IDs when present;
- referrer;
- original landing page;
- a canonical landing page with common tracking parameters removed.

## Default channel rules

The example classifies common patterns into:

- `paid_search`
- `paid_social`
- `email`
- `organic_search`
- `organic_social`
- `referral`
- `direct`
- `other`

These are explicit starter rules. Adapt them to your own acquisition taxonomy before using them in reporting.

## Setup

1. Import `workflow.json`.
2. Use the test webhook URL.
3. POST `sample-request.json`.
4. Verify the normalized output.
5. Edit source/channel rules to match your analytics conventions.
6. Send the normalized object into your CRM, database, analytics pipeline, or lead workflow.

## Limitations

- Channel classification is rule-based, not an authoritative analytics attribution model.
- The workflow does not resolve cross-session or multi-touch attribution.
- Invalid/non-absolute landing URLs are returned unchanged.
- Removing tracking query parameters from the canonical URL does not alter the original value.
