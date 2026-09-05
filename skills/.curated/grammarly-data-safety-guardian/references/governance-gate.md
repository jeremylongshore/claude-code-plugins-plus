# Submission governance gate

The preflight separates provider constraints from local authority:

| Gate | Evidence | Failure behavior |
|---|---|---|
| Content binding | Reviewed `content_sha256` from the evaluator dry run | Repeat review if bytes change |
| Classification | Explicit known class; `restricted` blocked | Escalate to the policy owner |
| Ownership | `data_owner_approved: true` | Stop |
| Consent | `consent_confirmed: true` | Stop |
| Transfer | `transfer_approved: true` | Stop |
| Retention | Provider 24-hour document and 30-day score boundaries acknowledged | Stop |
| API destination | Exact `https://api.grammarly.com` control-plane origin | Stop |
| Byte destination | Exact sanitized public HTTPS S3 origin from `--inspect-upload-origin`, separately approved | Stop |

A positive answer in one gate does not satisfy another. Keep evidence records in the
system that owns them; this manifest stores only decisions. Never attach text,
screenshots, ticket bodies, approver identities, filenames, source paths, tokens,
full presigned URLs, or provider responses. The upload origin is retained because it
is the minimum non-secret destination fact required for approval.

`INSPECTION_READY` means every gate except the not-yet-discovered byte origin passed;
it permits only OAuth job creation with the normalized filename `document.<extension>`
and no document bytes. `READY` permits only progression to the separately controlled evaluator. It is not
legal advice, proof of consent, a content-quality judgment, or authority to use a
different destination.

Provider facts checked 2026-09-04 against the official
[Writing Score API](https://developer.grammarly.com/writing-score-api.html),
[AI Detection API](https://developer.grammarly.com/ai-detection-api.html), and
[Plagiarism Detection API](https://developer.grammarly.com/plagiarism-detection-api.html).
