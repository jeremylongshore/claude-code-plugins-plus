# ClaimCenter Workflow — API Reference

State-transition endpoints, request shapes, and authorization tiers for the patterns in `SKILL.md`.

## Claim state machine

```
FNOL ──► Open ──► (Investigation) ──► Settled ──► Closed
                       │                              │
                       ├─► Pending(SIU) ──► resumed ──┘
                       └─► Denied ─────────────────────┘
                                                       │
                                  late evidence ◄──────┴──► Reopened ──► Closed
```

`Closed` is reversible via the `/reopen` endpoint within the carrier's retention window. Beyond retention, a new claim is the only path.

## Claim endpoints

| Method | Path | Purpose |
|---|---|---|
| POST | `/cc/rest/v1/claims` | FNOL — creates a new claim |
| GET | `/cc/rest/v1/claims?filter=...` | search (used for dedup pre-check) |
| GET | `/cc/rest/v1/claims/{id}?included=exposures,reserves,activities,payments` | fetch with full context (use for settlement readiness) |
| PATCH | `/cc/rest/v1/claims/{id}` | update attributes — checksum required |
| POST | `/cc/rest/v1/claims/{id}/close` | settle and close |
| POST | `/cc/rest/v1/claims/{id}/reopen` | reopen a closed claim |

### FNOL request shape

```json
POST /cc/rest/v1/claims
Idempotency-Key: <UUID>

{
  "data": {
    "attributes": {
      "lossDate": "2026-04-15T14:30:00Z",
      "lossCause": { "code": "vehcollision" },
      "lossType": { "code": "AUTO" },
      "policyNumber": "PA-000123",
      "description": "Rear-end collision at intersection",
      "reporter": {
        "firstName": "Jane", "lastName": "Doe",
        "primaryPhone": { "phoneNumber": "555-0100" }
      }
    }
  }
}
```

`lossDate` is required and used in the dedup key. `policyNumber` ties to a PolicyCenter resource; if PC and CC share a tenant the link is automatic, otherwise a manual policy resolution step is required.

## Dedup key construction

| Loss type | Recommended dedup key |
|---|---|
| `AUTO` | `policyNumber + lossDate + lossCause` |
| `PROPERTY` | `policyNumber + lossDate + lossCause + lossLocation.zip` |
| `WORKERSCOMP` | `policyNumber + lossDate + employee.id` |
| `LIABILITY` | `policyNumber + lossDate + claimant.id` |

Configure dedup per line — the auto key is too narrow for property storms (multiple distinct losses on the same date) and too broad for workers' comp (multiple legitimate same-employee claims would dedup incorrectly without the employee id).

## Reserve endpoints

| Method | Path | Purpose |
|---|---|---|
| GET | `/cc/rest/v1/claims/{id}/reserves` | list reserves on a claim |
| POST | `/cc/rest/v1/claims/{id}/reserves` | create a reserve |
| PATCH | `/cc/rest/v1/reserves/{id}` | adjust reserve amount (checksum required) |
| POST | `/cc/rest/v1/reserves/{id}/transfer` | transfer reserve between cost categories |

### Reserve request shape

```json
{
  "data": {
    "attributes": {
      "reserveAmount": { "amount": 5000, "currency": "usd" },
      "costType": { "code": "claimcost" },
      "costCategory": { "code": "body" },
      "reserveLine": { "exposure": { "id": "cc:exposure:42" } }
    }
  }
}
```

`costCategory` codes are carrier-configurable — `body`, `parts`, `medical`, `legal`, `subro`, `salvage` are common defaults.

### Reserve adjustment rules

- New reserve amount **must** be ≥ cumulative payments in the same cost category
- Lowering below cumulative payments → `422 reserve-below-payments`
- Increasing has no upper bound at the API level (carrier authorization may block via separate workflow)
- Reserve at zero with no open exposure → eligible for close

## Payment endpoints

| Method | Path | Purpose |
|---|---|---|
| POST | `/cc/rest/v1/claims/{id}/payments` | create a payment (may land in PendingApproval) |
| GET | `/cc/rest/v1/payments/{id}` | check status |
| POST | `/cc/rest/v1/payments/{id}/approve` | supervisor approval (requires elevated role) |
| POST | `/cc/rest/v1/payments/{id}/reject` | supervisor rejection |

### Payment status lifecycle

```
Requested ──► PendingApproval ──► Approved ──► Issued
     │              │                              │
     │              └─► Rejected                   ├─► Cleared (bank confirmed)
     │                                             └─► Voided (issued in error)
     └─► AutoApproved (within authorization tier)
```

`AutoApproved` is the happy path — the integration's authorization tier covered the amount.
`PendingApproval` requires a human or a supervisor-tier integration to approve.

### Payment authorization tier

Configured per Service Application in **GCC > Identity & Access > Applications > [your-app] > Authorization Tier**. Common tiers:

| Tier | Limit |
|---|---|
| Tier 1 (auto) | $5,000 |
| Tier 2 (supervisor) | $25,000 |
| Tier 3 (manager) | $100,000 |
| Tier 4 (executive) | unlimited |

Carrier-configurable; treat the table as illustrative.

## Settlement readiness

Before calling `/close`, all of:

- Every Open exposure has been paid in full, denied, or has a zero reserve
- Every required activity (`activity.attributes.required === true`) has `status.code === "Completed"`
- No payments are in `Requested` or `PendingApproval`
- For lines that require it: subrogation decision recorded, salvage decision recorded

Calling close with any of the above unresolved returns:

```json
{ "userMessage": "Claim cannot be closed — open items present", "errors": [{ "type": "close-blocked" }] }
```

The error response does not enumerate which items are blocking; the integration must inspect them itself via the included resources.

## Reopen endpoint

```json
POST /cc/rest/v1/claims/{id}/reopen
{
  "data": { "attributes": { "reason": "Late evidence — body shop final invoice" } }
}
```

Reason is required and audit-logged. Reopen is rejected if the claim is past the carrier's reopen-retention window (commonly 1–3 years post-close); past that, a new claim is the only path, and the relationship to the prior loss event must be documented in claim notes.

## Activities

Activities are the to-do system inside ClaimCenter — assignments to adjusters, document reviews, and SLA-tracked tasks. The integration cares about the `required` flag (gates settlement) and the `assignedTo` field (escalation routing).

```http
GET /cc/rest/v1/claims/{id}/activities
```

```json
{
  "data": [
    {
      "attributes": {
        "subject": "Confirm subrogation decision",
        "required": true,
        "status": { "code": "Open" },
        "dueDate": "2026-05-01T00:00:00Z",
        "assignedTo": { "id": "user:adjuster-42" }
      }
    }
  ]
}
```

## Related references

- `references/implementation-guide.md` — extended walkthrough
- Sibling `guidewire-install-auth/references/API_REFERENCE.md` — auth endpoints, JWT structure
- Sibling `guidewire-sdk-patterns/references/API_REFERENCE.md` — Cloud API envelope, pagination, error response shapes
- Sibling `guidewire-core-workflow-a/references/API_REFERENCE.md` — PolicyCenter workflow this can integrate with via shared policy reference
