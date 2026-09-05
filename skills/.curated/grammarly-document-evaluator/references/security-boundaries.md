# Security and retention boundaries

Verified against official Grammarly documentation on 2026-09-04.

- API access is limited to Grammarly Enterprise and institution-wide Grammarly for
  Education customers with administrator-created OAuth credentials.
- Keep client credentials in an approved secret store and inject them as
  `GRAMMARLY_CLIENT_ID` and `GRAMMARLY_CLIENT_SECRET`. Never paste them into prompts,
  files, command arguments, logs, or diagnostic bundles.
- A supported document is `.doc`, `.docx`, `.odt`, `.txt`, or `.rtf`, at most 4,194,304
  bytes, at most 100,000 extracted characters, and at least 30 words. Binary formats
  cannot have extraction counts verified safely before provider processing.
- Grammarly says documents are retained only as needed for analysis and no longer than
  24 hours; scores remain accessible through the API for 30 days. These provider
  boundaries do not replace the operator's consent, classification, or retention policy.
- Presigned upload URLs are credentials. Do not log, persist, follow redirects from, or
  send bearer tokens to them.
- Require a content-bound `INSPECTION_READY` safety manifest before inspection obtains
  OAuth or creates a normalized-filename provider job. No document bytes are sent.
- Use `--inspect-upload-origin` to emit only scheme and authority. Approve that exact
  origin in the data-safety manifest; execution creates a new request and refuses PUT
  when the newly issued origin differs.
- Hostnames are resolved before create acceptance and again at the upload sink; every
  returned address must be globally routable. The upload TLS connection uses one of
  those validated addresses while preserving SNI and certificate verification for the
  approved hostname, closing the DNS validation/connection gap.
- The egress allowlist is fail-closed to S3-shaped hosts under `amazonaws.com` on the
  default HTTPS port, based on the host form shown by
  Grammarly's official presigned-upload example. A different provider host requires a
  reviewed contract update; it is not accepted dynamically.
- Exact path and query approval is intentionally excluded because the presigned URL is
  a short-lived secret issued by Grammarly after approval. It remains in memory, is
  hashed for correlation, never redirected, and is trusted only as a capability from
  the authenticated control plane on the separately approved origin.
- Hashes are correlation handles, not proof that content is anonymous. Protect the
  source document and any downstream score receipt according to its classification.

Sources: [OAuth credentials](https://developer.grammarly.com/oauth-credentials.html),
[first API request](https://developer.grammarly.com/your-first-api-request.html), and
[Writing Score API](https://developer.grammarly.com/writing-score-api.html).
