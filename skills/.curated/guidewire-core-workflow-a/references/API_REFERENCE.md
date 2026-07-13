# PolicyCenter Workflow — API Reference

State-transition endpoints, request shapes, and observable side effects for the patterns in `SKILL.md`.

## State machine

```
Account ──► Submission(Draft) ──► Submission(Quoted) ──► Submission(Bound) ──► Policy(In Force)
                                       │                       │                       │
                                       └─► Withdrawn           └─► Bound (no issue)    ├─► Endorsement(Draft → Bound)
                                                                                       ├─► Renewal(Draft → Bound → In Force)
                                                                                       └─► Cancellation
```

`Bound` does not equal `In Force`. A bound submission produces a Policy resource that is invisible to billing until `issue` is called.

## Account endpoints

| Method | Path | Purpose |
|---|---|---|
| POST | `/pc/rest/v1/accounts` | create account |
| GET | `/pc/rest/v1/accounts/{id}` | fetch by resource id |
| GET | `/pc/rest/v1/accounts?filter=accountNumber+eq+'A000001'` | fetch by account number |
| PATCH | `/pc/rest/v1/accounts/{id}` | update — checksum round-trip required |

`accountHolderContact` is required and contains the primary insured's contact info (Person or Company sub-type). `producerCodes` ties the account to a broker hierarchy and is required for broker-portal scenarios.

## Submission (jobs) endpoints

| Method | Path | Purpose | State transition |
|---|---|---|---|
| POST | `/pc/rest/v1/jobs/submissions` | create submission | → Draft |
| POST | `/pc/rest/v1/jobs/{id}/quote` | request quote | Draft → Quoted |
| POST | `/pc/rest/v1/jobs/{id}/bind` | bind | Quoted → Bound |
| POST | `/pc/rest/v1/jobs/{id}/issue` | issue (commit to In Force) | Bound → In Force (creates Policy) |
| POST | `/pc/rest/v1/jobs/{id}/withdraw` | withdraw | * → Withdrawn |
| PATCH | `/pc/rest/v1/jobs/{id}` | edit attributes (e.g., add coverages) | only valid in Draft |

### Quote response — underwritingIssues structure

```json
{
  "data": {
    "attributes": {
      "totalPremium": 1234.56,
      "quoteExpirationDate": "2026-06-15T23:59:59Z",
      "underwritingIssues": [
        {
          "id": "uw:42",
          "shortDescription": "High-value vehicle requires manual review",
          "issueType": { "code": "HighValueVehicle" },
          "status": "Open",
          "blocksBind": true,
          "currentBlockingPoint": "BindingBlocked"
        }
      ]
    }
  }
}
```

The `blocksBind` boolean is the gate. Issues with `blocksBind: false` are informational; bind succeeds with them present. Always check the boolean per issue, not the array length.

### Quote-expiry detection

`attributes.quoteExpirationDate` is an ISO-8601 timestamp. After expiry, `bind` returns:

```json
{
  "userMessage": "Quote has expired",
  "errors": [{ "type": "quote-expired", "message": "Quote expired on 2026-06-15T23:59:59Z" }]
}
```

Re-quote rather than retrying bind directly.

## Policy lifecycle endpoints

| Method | Path | Purpose |
|---|---|---|
| GET | `/pc/rest/v1/policies/{id}` | fetch the in-force policy |
| GET | `/pc/rest/v1/policies/{id}?included=lines,coverages` | fetch with line-of-business detail |
| POST | `/pc/rest/v1/policies/{id}/endorse` | open an endorsement job |
| POST | `/pc/rest/v1/policies/{id}/renew` | open a renewal job |
| POST | `/pc/rest/v1/policies/{id}/cancel` | open a cancellation job |

Endorsement, renewal, and cancellation each spawn a new job (Submission-like resource) that goes through Draft → Quoted → Bound → applied. The original policy stays in force until the job binds.

### Renewal-window check

```http
GET /pc/rest/v1/policies/{id}
```

Inspect `attributes.expirationDate` and the product's renewal-window configuration. Calling `/renew` outside the window:

```json
{ "userMessage": "Renewal window not open", "errors": [{ "type": "renewal-window-closed" }] }
```

The renewal window is product-specific and configured in PolicyCenter. Read it from the product configuration endpoint, or accept the rejection and back off until the window opens.

### Endorsement premium-drift detection

```http
GET /pc/rest/v1/policies/{id}                              → currentPolicy.totalPremium
POST /pc/rest/v1/policies/{id}/endorse                     → endorsement (Draft)
POST /pc/rest/v1/jobs/{endorsementId}/quote                → endorsement.totalPremium
```

Compare `endorsement.totalPremium` against `currentPolicy.totalPremium`. Drift > threshold should emit a finance-integration event before `bind`. Common cause of drift: rate plan version change between policy inception and endorsement effective date.

## State-transition log (recommended)

Every API call in the workflow should be persisted to a state-transition log table:

| Column | Content |
|---|---|
| `correlation_id` | UUIDv4 — single ID across the full submission lifecycle |
| `idempotency_key` | the key sent on the request |
| `submission_id` / `policy_id` | resource id from the response |
| `transition` | `created`, `quoted`, `bound`, `issued`, `endorsement-quoted`, etc. |
| `request_body` | JSON, redacted of PII |
| `response_status` | HTTP status |
| `response_body` | JSON, redacted of PII |
| `at` | timestamp |

Without this log, debugging "why is this submission stuck in Quoted" requires re-running the full workflow against the API, which may be impossible if the policy effective date has passed.

## Common UW issue types

The `issueType.code` values you will see most often (varies by carrier configuration):

| Code | Trigger |
|---|---|
| `HighValueAccount` | premium above a configured threshold |
| `HighValueVehicle` | vehicle worth above a configured threshold |
| `PriorClaims` | claim history exceeds risk appetite |
| `UnderageOperator` | operator age below configured minimum |
| `LapseInCoverage` | gap in prior insurance |
| `RestrictedZIP` | account address in a restricted zone |
| `ManualReferral` | catch-all for product-specific manual paths |

These codes are configurable per carrier; treat the list as illustrative, not exhaustive.

## Related references

- `references/implementation-guide.md` — extended walkthrough
- Sibling `guidewire-install-auth/references/API_REFERENCE.md` — auth endpoints, JWT structure
- Sibling `guidewire-sdk-patterns/references/API_REFERENCE.md` — Cloud API envelope, pagination, error response shapes
- Sibling `guidewire-webhooks-integrations` — App Events fired on bind, issue, renewal transitions
