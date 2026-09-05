# Grammarly official API contract audit

**Audit date:** 2026-09-04

**Reverified date:** 2026-09-05

**Authority:** current official Grammarly developer documentation

**Outcome:** the v1 pack failed production accuracy and security review.

## Contracts audited against official documentation

OAuth client credentials use form encoding at
`https://auth.grammarly.com/v4/api/oauth2/token` with `grant_type`, `client_id`,
`client_secret`, and comma-separated `scope`. Official examples demonstrate
`access_token`; they do not document `expires_in`.

Writing Score, AI Detection, and Plagiarism Detection all use a document lifecycle:

1. POST `{ "filename": "document.ext" }` to the operation base.
2. Receive `score_request_id` and `file_upload_url`.
3. PUT bytes to the HTTPS presigned URL without a bearer token.
4. GET `<base>/<score_request_id>` until uppercase `PENDING`, `FAILED`, or `COMPLETED`.

| Operation | Base | Scopes | Score fields |
|---|---|---|---|
| Writing Score | `/ecosystem/api/v2/scores` | `scores-api:read`, `scores-api:write` | `general_score`, `engagement`, `correctness`, `delivery`, `clarity` |
| AI Detection (Beta) | `/ecosystem/api/v1/ai-detection` | `ai-detection-api:read`, `ai-detection-api:write` | `average_confidence`, `ai_generated_percentage` |
| Plagiarism (Beta) | `/ecosystem/api/v1/plagiarism` | `plagiarism-api:read`, `plagiarism-api:write` | `originality` |

Scores are `0..1`. Supported extensions are `.doc`, `.docx`, `.odt`, `.txt`, and
`.rtf`. Limits are 4,194,304 bytes, 100,000 extracted characters, and a documented
30-word minimum. Upload starts within 120 seconds. Documents are retained no longer
than 24 hours and scores remain available for 30 days. POST creation is documented at
10 requests/second, GET polling at 50 requests/second, with exponential backoff for 429
and an ideal two-second base. No processing SLA or required polling interval is stated.

Analytics is a read-only cursor-paginated API under
`/ecosystem/api/v2/analytics/users/`, requiring `analytics-api:read`. License reads use
`/ecosystem/api/v1/users` and `/invitees`, requiring `users-api:read`; destructive
license endpoints require `users-api:write`, return 204, and cannot remove admins.

## Official documentation inconsistencies

- The OAuth scope catalog omits AI Detection and Plagiarism scopes that their endpoint
  pages require. v2 cites the endpoint pages and flags the discrepancy for vendor
  confirmation.
- Analytics prose includes a trailing slash while an example omits it.
- The institution-summary heading includes `/v1`; an example omits `/v1`. v2 does not
  automate this endpoint.

## v1 findings that required removal

The 24 old skills included an incorrect OAuth host/path, missing scopes, direct JSON
text submission, invented `/v1/check`, `/v1/usage`, `/v1/account`, sandbox, RBAC, and
webhook contracts, wrong fields/scales/statuses, raw response and text logging, and a
fallback that fabricated scores during outages. Structural schema scores did not test
these behaviors.

## Primary sources

- [Developer portal](https://developer.grammarly.com/)
- [OAuth credentials and scope catalog](https://developer.grammarly.com/oauth-credentials.html)
- [First API request](https://developer.grammarly.com/your-first-api-request.html)
- [Writing Score API](https://developer.grammarly.com/writing-score-api.html)
- [AI Detection API](https://developer.grammarly.com/ai-detection-api.html)
- [Plagiarism Detection API](https://developer.grammarly.com/plagiarism-detection-api.html)
- [Analytics API](https://developer.grammarly.com/analytics-api.html)
- [License Management API](https://developer.grammarly.com/license-management-api.html)
- [Text Editor SDK general-availability history](https://www.grammarly.com/blog/company/general-availability-grammarly-text-editor-sdk/)
