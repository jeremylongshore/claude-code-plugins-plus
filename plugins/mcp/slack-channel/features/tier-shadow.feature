# SPDX-License-Identifier: Apache-2.0
# Feature owner: engineer. AI tooling may add glue (step definitions,
# runners) but MUST NOT edit the scenarios below. See features/README.md.
#
# Primitive: detectShadowing() in policy.ts — cross-tier intersection lint.
# Anchor: "Cross-tier intent must be explicit — a lower-tier auto_approve
#          touching the same call space as a higher-tier deny is ambiguous,
#          not silently resolved."

Feature: Cross-tier shadow detection (ccsc-4g8)
  When a lower-tier auto_approve rule's match overlaps with a higher-
  tier (Admin) deny rule's match, the static linter must surface the
  intersection at load time. Pure within-tier subset detection cannot
  catch this class — the two rules live in different tiers, so subset
  containment is irrelevant. The check is for intersection: does any
  one concrete tool call exist that both rules would match? If yes,
  the operator's intent is ambiguous and the linter says so.

  Once ccsc-8pw lands and evaluate() acts on tier precedence, Admin
  deny will resolve in its favor — but the audit trail (which tier
  the call "really came from") is opaque to a downstream reader of
  the policy file unless the conflict is surfaced. The lint is the
  surface.

  Background:
    Given an empty list of policy rules

  Scenario: Workspace auto_approve intersecting Admin deny is flagged
    Given a workspace-tier auto_approve rule on tool "Bash"
    And an admin-tier deny rule on tool "Bash"
    When the linter runs
    Then it emits one cross-tier warning
    And the cross-tier warning names the workspace rule as later and the admin rule as earlier

  Scenario: User auto_approve intersecting Admin deny is flagged
    Given a user-tier auto_approve rule on tool "Write"
    And an admin-tier deny rule on tool "Write"
    When the linter runs
    Then it emits one cross-tier warning

  Scenario: Default-tier auto_approve intersecting Admin deny is flagged
    Given a default-tier auto_approve rule on tool "Read"
    And an admin-tier deny rule on tool "Read"
    When the linter runs
    Then it emits one cross-tier warning

  Scenario: Disjoint tools across tiers — no warning
    Given a workspace-tier auto_approve rule on tool "Bash"
    And an admin-tier deny rule on tool "Write"
    When the linter runs
    Then it emits no warnings

  Scenario: Admin auto_approve and workspace deny — no warning (intended direction)
    Given an admin-tier auto_approve rule on tool "Bash"
    And a workspace-tier deny rule on tool "Bash"
    When the linter runs
    Then it emits no warnings

  Scenario: Two admin rules in the same tier — within-tier subset still detected
    Given an admin-tier deny rule on tool "Bash"
    And a second admin-tier deny rule on tool "Bash"
    When the linter runs
    Then it emits one within-tier warning

  Scenario: Channel-scoped intersection with Admin deny is flagged
    Given a workspace-tier auto_approve rule on tool "Bash" in channel "C001"
    And an admin-tier deny rule on tool "Bash"
    When the linter runs
    Then it emits one cross-tier warning

  Scenario: Disjoint channels — no warning
    Given a workspace-tier auto_approve rule on tool "Bash" in channel "C001"
    And an admin-tier deny rule on tool "Bash" in channel "C999"
    When the linter runs
    Then it emits no warnings

  Scenario: pathPrefix overlap is detected
    Given a workspace-tier auto_approve rule with pathPrefix "/home/jeremy/projects"
    And an admin-tier deny rule with pathPrefix "/home/jeremy"
    When the linter runs
    Then it emits one cross-tier warning

  Scenario: argEquals agreement on shared keys — intersection
    Given a workspace-tier auto_approve rule on tool "Bash" with argEquals command equal to "ls"
    And an admin-tier deny rule on tool "Bash" with argEquals command equal to "ls"
    When the linter runs
    Then it emits one cross-tier warning

  Scenario: argEquals disagreement on shared keys — no intersection
    Given a workspace-tier auto_approve rule on tool "Bash" with argEquals command equal to "ls"
    And an admin-tier deny rule on tool "Bash" with argEquals command equal to "rm"
    When the linter runs
    Then it emits no warnings

  Scenario: argEquals on disjoint keys — intersection
    Given a workspace-tier auto_approve rule on tool "Bash" with argEquals cwd equal to "/tmp"
    And an admin-tier deny rule on tool "Bash" with argEquals command equal to "ls"
    When the linter runs
    Then it emits one cross-tier warning

  Scenario: actor mismatch — no intersection
    Given a workspace-tier auto_approve rule on tool "Bash" with actor "session_owner"
    And an admin-tier deny rule on tool "Bash" with actor "claude_process"
    When the linter runs
    Then it emits no warnings

  Scenario: Admin deny against non-Admin require_approval — no warning
    Given a workspace-tier require_approval rule on tool "Bash"
    And an admin-tier deny rule on tool "Bash"
    When the linter runs
    Then it emits no warnings

  Scenario: Multiple admin denies, only one intersects
    Given a workspace-tier auto_approve rule on tool "Bash"
    And an admin-tier deny rule on tool "Bash"
    And an admin-tier deny rule on tool "Write"
    When the linter runs
    Then it emits one cross-tier warning
    And the cross-tier warning earlier id matches the bash admin rule
