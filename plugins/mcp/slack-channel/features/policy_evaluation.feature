# SPDX-License-Identifier: MIT
# Feature owner: engineer. AI tooling may add glue (step definitions,
# runners) but MUST NOT edit the scenarios below. See features/README.md.
#
# Primitive: evaluate() in policy.ts — declarative policy engine.
# Anchor: "Declarative policy engine — three effects only; more is a footgun for shadows."

Feature: Policy evaluation (first-applicable)
  The policy evaluator walks rules in the order the operator authored
  them and returns on the first match. Three effects exist: auto
  approval, denial, and require-approval. No compound combinators, no
  expression DSL — only three effects, because more would be a
  footgun for shadows. A tool call with no matching rule falls to a
  default branch: deny when the tool is in the operator's
  require-authored-policy set, allow otherwise.

  Background:
    Given a tool call addressed at a session with a known channel and actor
    And an approvals map seeded for this session

  Scenario: The first auto_approve match short-circuits evaluation
    Given a rule list whose first matching rule has an auto_approve effect
    When the evaluator processes a matching tool call
    Then the decision is allow
    And the decision cites the matched rule id

  Scenario: The first deny match short-circuits evaluation with the authored reason
    Given a rule list whose first matching rule has a deny effect
    When the evaluator processes a matching tool call
    Then the decision is deny
    And the decision carries the authored reason string

  Scenario: A require_approval match with no prior approval yields a require decision
    Given a rule list whose first matching rule requires human approval
    And no approval is recorded for the rule and session key
    When the evaluator processes a matching tool call
    Then the decision is require
    And the decision carries the configured approval TTL

  Scenario: A require_approval match with a live approval yields allow
    Given a rule list whose first matching rule requires human approval
    And a live approval is recorded for the rule and session key
    When the evaluator processes a matching tool call
    Then the decision is allow
    And the decision cites the matched rule id

  Scenario: A require_approval match with an expired approval re-triggers the require path
    Given a rule list whose first matching rule requires human approval
    And an expired approval is recorded for the rule and session key
    When the evaluator processes a matching tool call at a later time
    Then the decision is require
    And the expired approval does not satisfy the check

  Scenario: A tool with no matching rule and no require-authored entry defaults to allow
    Given a rule list where no rule matches the tool call
    And the require-authored-policy set does not contain the tool name
    When the evaluator processes the tool call
    Then the decision is allow

  Scenario: A tool with no matching rule but a require-authored entry defaults to deny
    Given a rule list where no rule matches the tool call
    And the require-authored-policy set contains the tool name
    When the evaluator processes the tool call
    Then the decision is deny
    And the decision reason names the default-deny branch
