# Lindy Performance Tuning -- Safety and Rollback Details

## Non-Negotiable Invariants

Performance work must not weaken:

- Ask for Confirmation or draft mode for actions affecting people or records;
- integration authorization scope and tenant/workspace boundaries;
- input validation, output schema checks, and error routing;
- redaction, data minimization, retention, and audit requirements;
- loop limits, agent exit conditions, and fallback paths; or
- task evidence needed to investigate failures.

Treat any invariant change as a separate security/governance proposal, not as a
performance optimization.

## Safe Test Boundary

Lindy's Test Panel executes actual actions. Use synthetic fixtures, test accounts,
sandbox endpoints, and confirmations. Offline evals simulate the agent against
selected historical/reference tasks and do not execute real actions, but they still
consume workspace resources and may evaluate sensitive historical content inside
Lindy. Do not export that content into the experiment receipt.

## Loop Tuning

Max Concurrent is not a universal speed dial. Set it to `1` when iterations depend on
each other, modify shared state, require ordering, or face a strict downstream limit.
For independent items, increase it by one controlled step and measure error/rate-limit
behavior. Always cap Max Cycles from the bounded input size plus a documented safety
margin. Export only the minimum loop result needed downstream.

## Cache Decision Checklist

Before introducing any cache, answer:

1. Is the data safe and authorized to retain outside the source action?
2. What tenant/user key prevents cross-context reuse?
3. What invalidates the entry after source or permission changes?
4. What TTL and deletion path satisfy retention policy?
5. Could a stale result cause a message, update, payment, or access decision?
6. Does the same fixture/eval cohort prove correctness with and without the cache?

If these answers are missing, do not cache. Never hash a full customer payload and
treat the hash as sufficient isolation; authorization and invalidation still apply.

## Rollback Procedure

1. Pause or constrain the candidate rollout when any declared threshold fires.
2. Open Version History and restore the recorded known-good version.
3. Save and test the restored version with sanitized fixtures.
4. Confirm approvals, integration scopes, trigger filters, loop caps, and fallbacks.
5. Watch Tasks until the baseline behavior is re-established.
6. Record the failed hypothesis and evidence before attempting another single change.

## Troubleshooting Decisions

| Observation | Next controlled experiment |
|---|---|
| One block dominates p95 | Change that block's prompt/model/config only |
| Quality varies with shorter context | Restore context; test retrieval scope separately |
| High task volume comes from irrelevant triggers | Add one filter and measure false negatives |
| Parallel loop raises failures | Restore prior concurrency and inspect dependency limits |
| Candidate saves usage but changes approvals | Reject; safety gate has priority |

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
