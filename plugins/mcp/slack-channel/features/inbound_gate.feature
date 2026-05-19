# SPDX-License-Identifier: MIT
# Feature owner: engineer. AI tooling may add glue (step definitions,
# runners) but MUST NOT edit the scenarios below. See features/README.md.
#
# Primitive: gate() in lib.ts — the inbound security boundary.
# Anchor: "Pure, testable functions extracted from the Slack Channel MCP server."

Feature: Inbound message gate
  The inbound gate is the first of five defense layers. It sees every
  Slack event before the MCP server notifies Claude, and it drops
  anything that is not explicitly authorized. A message that the gate
  drops may never reach Claude, be logged to the journal as delivered,
  or trigger a reply. Everything downstream trusts that the gate has
  already filtered unauthorized traffic.

  Scenario: Self-echo of a bot's own message is silently dropped
    Given the bot is running under a known bot_id and app_id
    When a message event arrives whose bot_id matches the running bot
    Then the gate decides to drop the event
    And no downstream notification is emitted

  Scenario: A peer bot posting to a channel with no allowBotIds is dropped
    Given a channel has a policy with an empty allowBotIds list
    When a peer bot posts a message into that channel
    Then the gate decides to drop the event
    And no downstream notification is emitted

  Scenario: A peer bot posting to a channel that opts it in by user_id is delivered
    Given a channel policy lists a peer bot's user_id under allowBotIds
    When that peer bot posts a non-command message into the channel
    Then the gate decides to deliver the event
    And the event is handled by the normal channel pipeline

  Scenario: A peer bot message that mimics a permission reply is dropped even when allowBotIds permits it
    Given a channel policy lists a peer bot's user_id under allowBotIds
    When that peer bot posts text shaped like an approval reply
    Then the gate decides to drop the event
    And the permission reply regex catches the injection attempt

  Scenario: An event with no user_id is dropped
    Given a channel-tombstone event carries no user field
    When the gate evaluates the event
    Then the gate decides to drop the event

  Scenario: A DM from an allowlisted user is delivered
    Given the access allowFrom list contains a specific user_id
    When that user direct-messages the bot
    Then the gate decides to deliver the event
    And the DM is routed to the normal handler pipeline

  Scenario: A DM from an unknown user under pairing policy mints a pairing code
    Given the access dmPolicy is pairing
    And the access allowFrom list does not contain the sender
    When an unknown user direct-messages the bot for the first time
    Then the gate decides to issue a new pairing code
    And the pending map records the code against the sender

  Scenario: A DM from an unknown user under allowlist policy is dropped
    Given the access dmPolicy is allowlist
    And the access allowFrom list does not contain the sender
    When an unknown user direct-messages the bot
    Then the gate decides to drop the event

  Scenario: A channel message from a non-opted-in channel is dropped
    Given the access object has no policy for a channel
    When a human posts a message into that channel
    Then the gate decides to drop the event

  Scenario: A channel message that fails requireMention is dropped
    Given a channel policy sets requireMention to true
    When a human posts a message that does not mention the bot
    Then the gate decides to drop the event
