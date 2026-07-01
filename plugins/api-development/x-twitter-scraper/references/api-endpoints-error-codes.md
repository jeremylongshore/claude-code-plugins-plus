# Xquik REST API Endpoints: Error Codes

| Status | Code | Meaning |
|--------|------|---------|
| 400 | `invalid_input` | Request body failed validation |
| 400 | `invalid_id` | Path parameter is not a valid ID |
| 400 | `invalid_json` | Invalid JSON in request body |
| 400 | `invalid_tweet_url` | Tweet URL format is invalid |
| 400 | `invalid_tweet_id` | Tweet ID is empty or invalid |
| 400 | `invalid_username` | X username is empty or invalid |
| 400 | `invalid_tool_type` | Extraction tool type not recognized |
| 400 | `invalid_format` | Export format not `csv`, `json`, `md`, `md-document`, `pdf`, `txt`, or `xlsx` |
| 400 | `invalid_params` | Export query parameters are missing or invalid |
| 400 | `missing_query` | Required query parameter is missing |
| 400 | `missing_params` | Required query parameters are missing |
| 400 | `no_media` | Tweet has no downloadable media |
| 400 | `webhook_inactive` | Webhook is disabled (test-webhook only) |
| 401 | `unauthenticated` | Missing or invalid API key |
| 403 | `account_needs_reauth` | X account session expired; use dashboard re-auth flow |
| 402 | `no_subscription` | No active plan |
| 402 | `subscription_inactive` | Plan is not active |
| 402 | `no_credits` | No credit balance record exists |
| 402 | `insufficient_credits` | Credit balance is too low |
| 403 | `api_key_limit_reached` | API key limit reached (100 max) |
| 404 | `not_found` | Resource does not exist |
| 404 | `user_not_found` | X user not found |
| 404 | `tweet_not_found` | Tweet not found |
| 404 | `style_not_found` | No cached style found |
| 404 | `draft_not_found` | Draft not found |
| 409 | `monitor_already_exists` | Duplicate monitor for same username |
| 422 | `login_failed` | Account connection failed; use dashboard re-auth flow |
| 429 | - | Rate limited. Retry with backoff |
| 429 | `x_api_rate_limited` | X data source rate limited. Retry |
| 500 | `internal_error` | Server error |
| 502 | `stream_registration_failed` | Stream registration failed. Retry |
| 502 | `x_api_unavailable` | X data source temporarily unavailable |
| 502 | `x_api_unauthorized` | X data source authentication failed. Retry |
