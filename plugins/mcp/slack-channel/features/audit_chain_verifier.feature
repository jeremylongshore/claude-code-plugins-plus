# SPDX-License-Identifier: MIT
# Feature owner: engineer. AI tooling may add glue (step definitions,
# runners) but MUST NOT edit the scenarios below. See features/README.md.
#
# Primitive: verifyJournal() in journal.ts — hash-chain integrity check.
# Anchor: "Tamper-evident audit journal — chain refuses mixed versions."

Feature: Audit chain verification
  The audit journal is tamper-evident — every event hashes over the
  prior event so any byte-level edit breaks the chain. The verifier
  is read-only: it never modifies the log, and it stops at the first
  break with enough context for an operator to locate the damage. A
  clean chain verifies in linear time; any mismatch, gap, or version
  skew is surfaced as a single structured break record.

  Scenario: A clean, monotonic chain verifies successfully
    Given an audit journal containing a valid sequence of events
    When the verifier reads the journal end-to-end
    Then the result reports ok
    And the events-verified count matches the number of records

  Scenario: A prevHash mismatch is reported at the breaking line
    Given an audit journal whose fifth event carries a tampered prevHash
    When the verifier reads the journal in order
    Then the result reports not-ok at the fifth line
    And the break reason names the prevHash chain break

  Scenario: A seq gap is reported at the gap line
    Given an audit journal whose sequence jumps from nine to eleven
    When the verifier reads the journal in order
    Then the result reports not-ok at the line with seq eleven
    And the break reason names the seq gap and the expected value

  Scenario: A version skew is reported at the mismatched event
    Given an audit journal whose fourth event declares a schema version other than one
    When the verifier reads the journal in order
    Then the result reports not-ok at the fourth line
    And the break reason names the version skew

  Scenario: A malformed line is reported as a parse or schema error
    Given an audit journal whose third line is not valid canonical JSON
    When the verifier reads the journal in order
    Then the result reports not-ok at the third line
    And the break reason mentions a parse or schema failure

  Scenario: An empty line in the middle of the journal is reported as structural damage
    Given an audit journal whose sixth line is blank
    When the verifier reads the journal in order
    Then the result reports not-ok at the sixth line
    And the break reason names structural damage

  Scenario: A missing journal file is reported without crashing
    Given no audit journal exists at the requested path
    When the verifier is invoked against the missing path
    Then the result reports not-ok
    And the break reason includes the underlying read failure
