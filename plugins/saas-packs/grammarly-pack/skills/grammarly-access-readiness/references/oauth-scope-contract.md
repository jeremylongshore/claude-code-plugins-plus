# Grammarly OAuth readiness contract

This is the closed metadata schema for `audit_oauth_config.py`, not an OAuth request
body. The helper never accepts a client ID, secret, token, response, or caller-supplied
copy of the official scope catalog.

```json
{
  "schema_version": "1",
  "access_tier": "enterprise",
  "oauth_client_configured": true,
  "configuration_source": "secret-manager-reference",
  "operations": ["writing-score", "analytics-read"],
  "granted_scopes": ["scores-api:read", "scores-api:write", "analytics-api:read"],
  "beta_scope_exception_approved": false
}
```

Allowed access tiers are `enterprise`, `education-institution-wide`, and
`unknown`. Allowed configuration sources are `environment-injected`,
`secret-manager-reference`, and `unknown`. The value is only a handling category;
do not include a path, vault name, account identifier, or secret reference.

| Operation | Exact required scopes |
|---|---|
| `writing-score` | `scores-api:read`, `scores-api:write` |
| `ai-detection` | `ai-detection-api:read`, `ai-detection-api:write` |
| `plagiarism` | `plagiarism-api:read`, `plagiarism-api:write` |
| `analytics-read` | `analytics-api:read` |
| `license-read` | `users-api:read` |

The script owns this mapping. Extra scopes block least-privilege readiness.
`users-api:write` appears in Grammarly's official catalog, but the v2 pack does not
admit, request, or approve it because this pack does not automate license deletion.
Direct shared-library token requests for this scope also fail closed.

On 2026-09-04, the OAuth catalog omitted the AI and plagiarism scopes that the
respective endpoint pages require. Any beta operation always emits that documentation
flag. It remains blocked unless the organization's authorized review explicitly sets
`beta_scope_exception_approved: true`; that approval does not prove provisioning or
replace a live provider authorization.

Sources: [OAuth credentials](https://developer.grammarly.com/oauth-credentials.html),
[first API request](https://developer.grammarly.com/your-first-api-request.html),
[Writing Score](https://developer.grammarly.com/writing-score-api.html),
[AI Detection](https://developer.grammarly.com/ai-detection-api.html),
[Plagiarism Detection](https://developer.grammarly.com/plagiarism-detection-api.html),
[Analytics](https://developer.grammarly.com/analytics-api.html), and
[License Management](https://developer.grammarly.com/license-management-api.html).
Accessed 2026-09-04.
