# Submission manifest contract

The manifest is metadata-only. It never contains document bytes, extracted text,
filename, path, upload URL, credential, response body, person identifier, or policy
record.

```json
{
  "schema_version": "1",
  "operation": "writing-score",
  "content_sha256": "sha256:0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
  "extension": ".txt",
  "byte_size": 1842,
  "text_character_count": 1260,
  "word_count": 210,
  "classification": "confidential",
  "data_owner_approved": true,
  "consent_confirmed": true,
  "transfer_approved": true,
  "provider_retention_acknowledged": true,
  "api_control_plane_origin": "https://api.grammarly.com",
  "presigned_upload_origin": "https://grammarly-example.s3.amazonaws.com",
  "presigned_upload_origin_approved": true
}
```

The operation is `writing-score`, `ai-detection`, or `plagiarism`. The extension
is `.doc`, `.docx`, `.odt`, `.txt`, or `.rtf`; bytes are 1 through
4,194,304. UTF-8 text requires both derived counts, no more than 100,000 characters
and at least 30 words. Counts for binary formats are optional because provider
extraction cannot be reproduced safely from metadata.

Classification must be `public`, `internal`, `confidential`, or `restricted`.
The guard blocks `restricted` by default; relabeling is not a bypass. The owning
governance process must make any exceptional transfer decision outside this tool.
The ownership, consent, transfer, and retention booleans must always be true; the
upload-origin approval becomes true only after inspection. `api_control_plane_origin` must exactly equal the
pinned Grammarly API origin. Before inspection, set `presigned_upload_origin` to JSON
`null` and `presigned_upload_origin_approved` to `false`; if every other gate passes,
the result is `INSPECTION_READY`, which authorizes only destination discovery and no
document upload. After inspection, `presigned_upload_origin` must be the exact public
HTTPS origin emitted by the evaluator: scheme and host only, never the signed path or
query, and the approval flag must be true. The origin must use an S3-shaped hostname
under `amazonaws.com` and the default HTTPS port, a fail-closed local policy pinned
from Grammarly's official upload example. The
evaluator creates a new job for execution
and refuses the upload if its newly issued origin differs. The content digest binds
this review to the evaluator dry run but is not an anonymity guarantee.

Origin approval is intentionally an egress-authority decision, not approval of the
secret path and query. The authenticated Grammarly control plane issues that
short-lived capability; the evaluator keeps it in memory, hashes it for correlation,
disables redirects, and sends it only through a TLS connection pinned to an address
validated for the approved S3 hostname.

Grammarly documents a 24-hour maximum document-retention boundary and 30-day score
availability. `provider_retention_acknowledged` confirms those provider facts were
considered; it does not claim local logs, receipts, backups, or downstream systems use
the same retention.

Sources: [Writing Score](https://developer.grammarly.com/writing-score-api.html),
[AI Detection](https://developer.grammarly.com/ai-detection-api.html), and
[Plagiarism Detection](https://developer.grammarly.com/plagiarism-detection-api.html).
Accessed 2026-09-04.
