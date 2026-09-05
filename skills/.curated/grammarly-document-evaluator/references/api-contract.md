# Grammarly document API contract

Verified against Grammarly's official developer documentation on 2026-09-04.

| Operation | Create and poll base | Required scopes | Completed score fields |
|---|---|---|---|
| Writing Score | `https://api.grammarly.com/ecosystem/api/v2/scores` | `scores-api:read`, `scores-api:write` | `general_score`, `engagement`, `correctness`, `delivery`, `clarity` |
| AI Detection (Beta) | `https://api.grammarly.com/ecosystem/api/v1/ai-detection` | `ai-detection-api:read`, `ai-detection-api:write` | `average_confidence`, `ai_generated_percentage` |
| Plagiarism Detection (Beta) | `https://api.grammarly.com/ecosystem/api/v1/plagiarism` | `plagiarism-api:read`, `plagiarism-api:write` | `originality` |

The lifecycle is identical: POST JSON `{ "filename": "document.ext" }`; receive
`score_request_id` and `file_upload_url`; expose only that URL's public HTTPS origin
for separate approval; PUT raw bytes only when a newly issued URL has the same exact
origin and without the bearer token; GET `<base>/<score_request_id>` until `PENDING`,
`FAILED`, or `COMPLETED`. Upload must begin within 120 seconds. Grammarly does not document a
required upload `Content-Type`, a maximum processing time, or a mandatory polling
interval. Creation must not be retried automatically because idempotency is not
documented.

Every score is `0..1`, not `0..100`. The create endpoint is documented at 10 requests
per second and poll at 50 requests per second. Grammarly recommends exponential
backoff for HTTP 429 with an ideal two-second base; this is guidance, not a quota or SLA.

Sources: [Writing Score API](https://developer.grammarly.com/writing-score-api.html),
[AI Detection API](https://developer.grammarly.com/ai-detection-api.html), and
[Plagiarism Detection API](https://developer.grammarly.com/plagiarism-detection-api.html).
