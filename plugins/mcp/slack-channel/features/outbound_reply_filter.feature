# SPDX-License-Identifier: MIT
# Feature owner: engineer. AI tooling may add glue (step definitions,
# runners) but MUST NOT edit the scenarios below. See features/README.md.
#
# Primitive: assertOutboundAllowed() in lib.ts — outbound reply filter.
# Anchor: "Pure, testable functions extracted from the Slack Channel MCP server."

Feature: Outbound reply filter
  The outbound gate ensures that replies only flow to (channel, thread)
  pairs that have previously delivered inbound OR to channels the
  operator has explicitly opted in. A tool call that ran in thread A
  may not post into thread B merely because both live in the same
  channel — cross-thread authority is not granted implicitly. This is
  the defense that stops a compromised session from broadcasting.

  Scenario: A reply into an opted-in channel succeeds regardless of thread state
    Given an access object opts the channel into the allowlist
    When the server attempts a reply at the top of that channel
    Then the gate allows the outbound message
    And the channel-level opt-in supersedes any thread-level delivery check

  Scenario: A reply into a thread that has previously delivered inbound succeeds
    Given a delivered-threads set records a prior inbound in a specific thread
    When the server attempts a reply into that same thread
    Then the gate allows the outbound message
    And the composite key matches the delivered entry

  Scenario: A reply into a thread with no prior inbound in an unopted channel is rejected
    Given the channel is not in the access allowlist
    And the delivered-threads set is empty for this thread
    When the server attempts a reply into that thread
    Then the gate throws an outbound-gate error
    And the error identifies the channel and thread that failed the check

  Scenario: A reply into thread B on behalf of thread A's session is rejected
    Given a delivered-threads set records thread A in an unopted channel
    When the server attempts a reply into thread B of the same channel
    Then the gate throws an outbound-gate error
    And cross-thread authority is denied

  Scenario: A top-level post into a channel with only threaded deliveries is rejected
    Given a delivered-threads set records a thread but no top-level delivery
    And the channel is not in the access allowlist
    When the server attempts a top-level post into that channel
    Then the gate throws an outbound-gate error
    And the top-level slot is distinct from any threaded slot
