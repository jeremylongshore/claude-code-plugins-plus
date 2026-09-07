# Lindy Change and Migration Evidence Guide

Use this guide for configuration changes, restores, template-based recreation,
and workspace moves. Lindy's workspace UI and retained run evidence are the
control surfaces; this workflow has no dependency on an SDK, package, API key,
CLI, or undocumented export endpoint.

## Contents

1. [Change record](#change-record)
2. [Dependency inventory](#dependency-inventory)
3. [Approval preservation](#approval-preservation)
4. [Clean test plan](#clean-test-plan)
5. [Cutover controls](#cutover-controls)
6. [Rollback proof](#rollback-proof)
7. [Evidence sufficiency](#evidence-sufficiency)

## Change Record

```markdown
# Lindy change <identifier>

Type: in-place / restore / template recreation / workspace move
Source workspace: <identifier>
Target workspace: <identifier or same>
Workflow: <identifier>
Change owner: <owner>
Approver: <approver>
Rollback owner: <owner>
Acceptance owner: <owner>
Rollback Version History entry: <name and observed timestamp>

## Intended differences

- <one bounded change>

## Explicit non-goals

- <out-of-scope workflow or side effect>

## Acceptance criteria

- <observable task result plus destination state>
```

Refer to secrets by secret-manager record name only. Do not paste secret values,
OAuth tokens, full webhook URLs, customer payloads, or personal data.

## Dependency Inventory

Inventory source and target separately. A source observation does not establish a
target fact.

| Dependency | Source evidence | Target evidence | Status | Owner |
|---|---|---|---|---|
| Trigger type and filters | UI receipt | UI receipt | status | owner |
| Actions and conditions | version/change review | candidate review | status | owner |
| Integration identity and scopes | redacted UI receipt | redacted UI receipt | status | owner |
| Knowledge sources | sanitized inventory | sanitized inventory | status | owner |
| Human approval | approver and rejection test | approver and rejection test | status | owner |
| Webhook destination | redacted fingerprint | redacted fingerprint | status | owner |
| External destinations | sandbox receipt | sandbox receipt | status | owner |
| Monitoring owner | runbook link | runbook link | status | owner |
| Rollback route | exercised procedure | exercised procedure | status | owner |

Allowed status values are `VERIFIED`, `FAILED`, `NOT VERIFIED`, and `N/A`. A
template can accelerate recreation, but its installation does not prove that any
workspace-bound dependency was transferred or preserved.

## Approval Preservation

For each action requiring human oversight, capture:

- the action or decision being held;
- the reviewer identity, group, or role;
- what context the reviewer receives;
- the approve, reject, timeout, and unavailable-reviewer paths;
- whether rejection prevents the downstream side effect; and
- a clean test receipt for each material path.

Do not equate a visually present approval node with an effective control. Exercise
the rejection path and verify the protected destination remains unchanged.

## Clean Test Plan

Lindy documents that the Test Panel executes workflows rather than simulating
them. Route every action to sandboxed destinations and use synthetic values.

| Case | Input | Expected task path | Expected destination evidence |
|---|---|---|---|
| Happy path | minimal valid synthetic event | expected branches complete | one sandbox side effect |
| Boundary value | maximum approved local size/count | accepted or rejected per contract | bounded result |
| Malformed input | wrong type or unknown field | validation branch | no external side effect |
| Missing authorization | disconnected or denied test integration | error branch | no protected side effect |
| Approval denied | synthetic high-risk action | rejection branch | no protected side effect |
| Downstream failure | controlled sandbox failure | documented failure branch | observable failure only |
| Duplicate event | same stable request ID twice | deduplicated behavior | at most one intended side effect |
| Restore candidate | known-good test fixture | baseline path | baseline destination state |

For every case, retain the Tasks-view task ID, step disposition, timestamps, and a
sanitized destination receipt. A task status alone does not prove the destination
effect; a destination effect alone does not prove the intended workflow produced it.

## Cutover Controls

Choose a cutover sequence from the actual architecture:

```text
approved candidate
  -> synthetic target verification
  -> controlled canary
  -> task and destination reconciliation
  -> remaining traffic
  -> acceptance owner decision
```

Define the canary size, observation window, stop conditions, and rollback trigger
in the change record. They are organization decisions, not fixed Lindy values.

If old and new workflows can reach the same non-idempotent destination, never feed
both the same production event. Use routing that has one active owner per event.
Keep the old workflow and route available until acceptance is documented.

For webhook callers, compare the target's generated webhook configuration to the
source. If a URL or generated secret differs, update the caller through its normal
secret/configuration deployment. Send the secret only to HTTPS on exact hostname
`public.lindy.ai` and the approved generated webhook path.

## Rollback Proof

### In-place restore

1. Select the recorded known-good entry in Version History.
2. Review the configuration loaded into the editor.
3. Save it, creating the new restored version documented by Lindy.
4. Run the clean rollback tests.
5. Verify the Tasks view and sandbox destination against the baseline.

### Workspace or routing rollback

1. Stop the candidate from receiving new events without deleting evidence.
2. Restore the prior approved route and any caller configuration.
3. Revalidate the prior authentication boundary.
4. Submit one clean event.
5. Match its task and destination result to the baseline.

Record partial or failed rollback explicitly. Loading a historical configuration,
changing routing, or seeing a 2xx response is not by itself rollback proof.

## Evidence Sufficiency

| Claim | Minimum evidence |
|---|---|
| Candidate matches intended change | reviewed change record plus target UI receipt |
| Workflow works | clean task receipt plus expected destination state |
| Approval is preserved | approve and reject receipts with destination verification |
| Webhook caller is migrated | target task correlated to unique clean request ID |
| Restore works | saved restored version plus clean baseline test |
| Migration is complete | all required dependencies verified and owner acceptance |

If evidence is absent, stale, indirect, or contradictory, the status is
`NOT VERIFIED` or `FAILED`; it is never silently promoted to `VERIFIED`.

## Official References

- [Version History](https://docs.lindy.ai/testing/version-history)
- [Test Panel](https://docs.lindy.ai/testing/test-panel)
- [Tasks](https://docs.lindy.ai/fundamentals/lindy-101/tasks)
- [Human in the Loop](https://docs.lindy.ai/testing/human-in-the-loop)
- [Templates](https://docs.lindy.ai/fundamentals/lindy-101/templates)
- [Workspaces](https://docs.lindy.ai/account-billing/workspaces)
- [Webhooks](https://docs.lindy.ai/skills/by-lindy/webhooks)
