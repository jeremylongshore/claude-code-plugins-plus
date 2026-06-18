# SPDX-License-Identifier: Apache-2.0
# Feature owner: engineer. AI tooling may add glue (step definitions,
# runners) but MUST NOT edit the scenarios below. See features/README.md.
#
# Primitive: dispatchAdminCommand() + parseAdminCommand() in admin.ts —
# operator-initiated admin verbs (!clear, !restart) with HMAC nonce +
# cross-channel HITL on destructive variants.
#
# Anchor: "Admin verbs are not chat content — no regex on inbound text
# can promote a message to an admin action without (a) channel + user
# allowlist AND (b) for destructive verbs, a server-minted HMAC nonce
# redeemed in the original channel." — THREAT-MODEL.md invariant #7
# (ccsc-o6x).

Feature: Operator admin commands (!clear / !restart) (ccsc-3w0)
  Slack operators on a channel's adminCommands.allowFrom list can
  type two admin verbs:
    - !clear (reversible): clears the bridge session state and sends
      a /clear keystroke to the Claude TUI via tmux send-keys.
      Runs without nonce friction — the cost of a stray !clear is one
      re-paste.
    - !restart (destructive): exits the Claude TUI via tmux send-keys
      /exit. Gated by HMAC nonce + cross-channel HITL per ccsc-ofn —
      the cost of a stray !restart is minutes of lost work.

  Both verbs route through the gate → parse → policy → journal →
  execute pipeline. admin.* events sign under journal v2 from day 1.
  admin.clear / admin.restart are VIRTUAL policy tools, NOT registered
  MCP tools — Claude cannot invoke them by tool call.

  Background:
    Given an admin command dispatcher with recording dependencies

  Scenario: Allowlisted operator issues !clear — full execution sequence
    Given the requester is on the channel's adminCommands.allowFrom list
    When the operator dispatches !clear
    Then the journal records admin.clear with outcome allow
    And supervisor.quiesceAndDeactivate was called
    And tmux received keys "/clear" "Enter"
    And a recycle reaction was posted

  Scenario: Non-allowlisted user issues !clear — denied, no execution
    Given the requester is NOT on the channel's adminCommands.allowFrom list
    When the operator dispatches !clear
    Then the dispatcher returns a denied outcome
    And the journal records admin.clear.denied
    And no tmux keys were sent

  Scenario: !restart with no nonce — challenge is issued
    Given the requester is on the channel's adminCommands.allowFrom list
    When the operator dispatches !restart without a nonce
    Then the dispatcher returns a challenge_issued outcome
    And the journal records admin.restart.challenge
    And no tmux keys were sent
    And the journal event does NOT contain the minted nonce

  Scenario: !restart with valid nonce — full execution sequence
    Given the requester is on the channel's adminCommands.allowFrom list
    And the verifier will return ok for the presented nonce
    When the operator dispatches !restart with a nonce
    Then the journal records admin.restart with outcome allow
    And tmux received keys "/exit" "Enter"
    And an arrows_counterclockwise reaction was posted

  Scenario: !restart with expired nonce — denied
    Given the requester is on the channel's adminCommands.allowFrom list
    And the verifier will return expired for the presented nonce
    When the operator dispatches !restart with a nonce
    Then the dispatcher returns a denied outcome with reason containing "expired"
    And the journal records admin.restart.denied
    And no tmux keys were sent

  Scenario: !restart with wrong-channel nonce — denied
    Given the requester is on the channel's adminCommands.allowFrom list
    And the verifier will return wrong-channel for the presented nonce
    When the operator dispatches !restart with a nonce
    Then the dispatcher returns a denied outcome with reason containing "wrong-channel"
    And the journal records admin.restart.denied

  Scenario: Non-allowlisted user with valid nonce — denied at allowlist, nonce not even verified
    Given the requester is NOT on the channel's adminCommands.allowFrom list
    When the operator dispatches !restart with a nonce
    Then the dispatcher returns a denied outcome
    And the verifier was NOT called

  Scenario: Journal ordering — record completes before side effects
    Given the requester is on the channel's adminCommands.allowFrom list
    When the operator dispatches !clear
    Then the journal write was observed before the tmux send-keys

  Scenario: Broken journal does NOT block execution — admin decision is authoritative
    Given the requester is on the channel's adminCommands.allowFrom list
    And the journal writer will throw on every write
    When the operator dispatches !clear
    Then tmux received keys "/clear" "Enter"
    And the dispatcher returns an executed outcome
