---
name: lindy-upgrade-migration
description: 'Manage Lindy agent configuration changes, platform updates, and migrations.

  Use when reconfiguring agents, handling platform changes,

  or migrating agents between workspaces.

  Trigger with phrases like "upgrade lindy", "lindy migration",

  "lindy reconfigure", "update lindy agents", "lindy workspace migration".

  '
allowed-tools: Read, Write, Edit
version: 1.20.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- lindy
- migration
compatibility: Compatible with AI coding agents that can read and edit Markdown evidence records
---
# Lindy Upgrade and Migration

## Overview

Plan and verify changes to Lindy workflows through the documented workspace UI.
Use Lindy's Version History as the in-place restoration mechanism, the Test Panel
for controlled execution, and the Tasks view for run evidence. Do not invent a
Lindy SDK, API key, package upgrade, CLI, export endpoint, or control plane.

Use **Read** to inspect the approved change record and evidence. Use **Write** or
**Edit** to maintain the migration record without copying secrets or customer data.

## Prerequisites

- Authorized access to every source and target workspace in scope.
- A named change owner, approver, rollback owner, and acceptance owner.
- A known-good saved agent version visible in Version History.
- A current inventory of triggers, actions, conditions, integrations, knowledge
  sources, manual approval steps, owners, and downstream side effects.
- Synthetic inputs and sandboxed destinations for Test Panel runs; its tests can
  execute real actions and call real external systems.
- Baseline task receipts from the Tasks view and explicit acceptance criteria.
- Current Lindy documentation and workspace evidence for any transfer or feature
  behavior relied upon by the change.

## Instructions

### Step 1: Define the change boundary

Record whether this is an in-place configuration change, restoration, template-
based recreation, or workspace move. List the exact workflows, integrations,
callers, secrets, data stores, approvers, and external side effects in scope.

Treat anything not documented by Lindy or directly observed in the target
workspace as `NOT VERIFIED`. Templates are starting workflows that must be
configured, customized, and tested; do not assume they preserve credentials,
triggers, knowledge, memories, phone or mail resources, permissions, approval
rules, webhook URLs, or other workspace-bound state.

### Step 2: Capture a rollback anchor and baseline

1. Save the current working workflow with a descriptive version name.
2. Open **Version History**, record the rollback version and review its changes.
3. Run approved synthetic cases and retain Tasks-view identifiers, step outcomes,
   and expected side effects.
4. Record current integration identities, trigger configuration, manual approval
   gates, and sanitized destination identifiers.

Do not copy OAuth tokens, webhook secrets, full payloads, or customer content into
the record.

### Step 3: Build the candidate safely

For an in-place change, edit the workflow but keep it inactive or otherwise
isolated until testing and approval are complete. For a workspace move, use a
documented template installation or recreate the workflow in the target workspace,
then verify every target-bound dependency individually.

If the target uses a webhook trigger, inspect its generated URL and secret. The
calling application may send that secret only to an HTTPS URL whose hostname is
exactly `public.lindy.ai` and whose path is the expected generated webhook path.
If the target URL or secret differs from the source, plan an atomic caller update;
do not infer whether copying or installing a template preserves either value.

Reconnect integrations through the target workspace UI. Preserve human-in-the-
loop approval by confirming the approval step, reviewer identity or role, timeout
behavior, and rejection path in the candidate—not merely by copying visible text.

### Step 4: Test with clean inputs

Use the Test Panel with synthetic data and sandboxed destinations. Test every
trigger and material condition branch, including malformed input, denied approval,
expired or missing authorization, external-action failure, duplicate delivery,
and recovery after a worker or downstream interruption.

The Test Panel performs real execution. Confirm each result in the panel and the
Tasks view, and reconcile expected side effects at the destination. A green step
without the expected destination state is not sufficient evidence.

### Step 5: Obtain approval and cut over

Present the evidence bundle and unresolved risks to the named approver. After
approval, use an owner-defined cutover method that prevents duplicate side effects.
Do not run old and new workflows in parallel against production inputs unless the
design proves idempotency and explicitly permits duplicate delivery.

Route a controlled canary where possible, observe Tasks-view results and downstream
state, then move remaining traffic. Keep the rollback target intact until the
acceptance owner signs off; do not delete it on a fixed timer.

### Step 6: Roll back when acceptance fails

For an in-place change, select the known-good entry in Version History, restore it,
review the loaded configuration, and save it. Lindy documents that saving a
restored configuration creates a new version rather than deleting later history.

For a workspace or endpoint cutover, restore the previously approved routing and
workflow state using the recorded change procedure. Revalidate authentication and
confirm a clean synthetic task. Rollback is complete only when the Tasks view and
destination evidence match the pre-change baseline.

### Step 7: Close with retained evidence

Record the final workflow version, task identifiers, approvals, observed outcomes,
cutover or rollback timestamps, remaining risks, and follow-up owners. Redact
secrets and minimize personal or customer data.

## Output

Produce a migration evidence bundle containing:

- change type, source and target workspaces, workflow identifiers, and owners;
- dependency inventory with `VERIFIED`, `FAILED`, `NOT VERIFIED`, or `N/A` status;
- rollback version and restoration procedure;
- clean-test cases and Tasks-view receipts for happy, failure, and approval paths;
- target integration, trigger, webhook, and destination verification;
- explicit approval and cutover decision;
- production observation and destination reconciliation; and
- final disposition: `MIGRATED`, `ROLLED BACK`, or `BLOCKED`, with open risks.

## Examples

### In-place configuration change

```markdown
# Change LND-42

- Boundary: prompt and one condition branch; no new integrations
- Rollback anchor: Version History entry "pre-LND-42"
- Clean tests: happy, denied approval, malformed input, destination failure
- Task receipts: task-a, task-b, task-c, task-d
- Human approval: VERIFIED -- reviewer role and rejection branch exercised
- Destination effects: VERIFIED against sandbox records
- Decision: MIGRATED
```

### Correct workspace-move decision

If a template installs but the target integration identity or approval path cannot
be verified, record that dependency as `NOT VERIFIED` and choose `BLOCKED`. Template
installation alone is not migration evidence.

## Error Handling

| Failure | Required response |
|---|---|
| No known-good Version History entry | Save and test a baseline before changing the workflow |
| Candidate test touches production data | Stop, contain the side effect, and replace it with clean test data |
| Target dependency behavior is undocumented | Verify directly or mark `NOT VERIFIED`; do not infer transfer behavior |
| Approval step or rejection path differs | Block cutover until the control is restored and tested |
| Webhook destination is not exact approved Lindy HTTPS host/path | Do not attach the trigger secret |
| Tasks evidence and destination state disagree | Treat acceptance as failed and investigate or roll back |
| Restore loads but is not saved and retested | Rollback remains incomplete |

## Resources

- [Lindy Version History](https://docs.lindy.ai/testing/version-history)
- [Lindy Test Panel](https://docs.lindy.ai/testing/test-panel)
- [Lindy Tasks](https://docs.lindy.ai/fundamentals/lindy-101/tasks)
- [Lindy Human in the Loop](https://docs.lindy.ai/testing/human-in-the-loop)
- [Lindy Templates](https://docs.lindy.ai/fundamentals/lindy-101/templates)
- [Lindy Workspaces](https://docs.lindy.ai/account-billing/workspaces)
- [Lindy Webhooks](https://docs.lindy.ai/skills/by-lindy/webhooks)
- [Detailed migration evidence guide](references/implementation-guide.md)
