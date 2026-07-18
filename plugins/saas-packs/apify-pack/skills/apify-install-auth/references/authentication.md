# Apify Authentication — Deep Reference

Detailed reference for how Apify authentication works, every place a token can
be supplied, and the full set of platform environment variables. The SKILL.md
covers the common path; drill in here when you need the complete picture.

## Auth Token Details

- Token format: `apify_api_` prefix followed by an alphanumeric string.
- Pass via `Authorization: Bearer YOUR_TOKEN` header (REST API).
- Pass via the `token` constructor option (JS client).
- The `APIFY_TOKEN` env var is auto-detected by both `apify-client` and the
  `apify` SDK, so if it is exported you usually do not pass `token` explicitly.

### Where a token can come from (precedence)

1. Explicit `token` option passed to `new ApifyClient({ token })`.
2. `APIFY_TOKEN` environment variable (auto-detected).
3. `apify login` CLI credentials stored in `~/.apify/auth.json` (CLI commands only).

For application code, prefer the environment variable so the same code runs
locally and on the Apify platform (where `APIFY_TOKEN` is injected for you).

## Environment Variable Reference

| Variable | Purpose |
|----------|---------|
| `APIFY_TOKEN` | API authentication (primary) |
| `APIFY_PROXY_PASSWORD` | Proxy access (auto-set on platform) |
| `APIFY_IS_AT_HOME` | `true` when running on the Apify platform |
| `APIFY_DEFAULT_DATASET_ID` | Default dataset for the current run |
| `APIFY_DEFAULT_KEY_VALUE_STORE_ID` | Default KV store for the current run |
| `APIFY_DEFAULT_REQUEST_QUEUE_ID` | Default request queue for the current run |

The `APIFY_DEFAULT_*` and `APIFY_IS_AT_HOME` variables are set automatically by
the Apify platform at Actor run time — you do not set them yourself in local
development.

## Security Notes

- Never commit `APIFY_TOKEN`. Add `.env` to `.gitignore`.
- Treat the token like a password: it grants full account access, including
  billing-relevant Actor runs.
- If a token leaks, regenerate it in Console > Settings > Integrations — the old
  value is revoked immediately.
