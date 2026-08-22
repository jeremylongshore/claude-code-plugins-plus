<!-- doc-class: record -->

# E7.3 Owner Action Packet — npm Production Lock

Status: owner-gated and not executed by the E7.3 code slice.

This packet completes the third publication boundary after the workflow lock and exact-SHA preflight. It requires an owner-controlled GitHub Environment; repository code, pull requests, and ordinary workflow edits must not be able to remove the protection.

## Preconditions

1. Confirm the canonical repository and the merged E7.3 code lock are present.
2. Confirm no repository-level `NPM_TOKEN` remains after migration.
3. Treat the prior npm token as potentially live until controlled replacement verification completes.
4. Have an owner-approved release test package and rollback window. Do not use an existing public package for an unapproved test.

## Owner-only setup

1. In GitHub, open Settings → Environments and create or inspect `npm-production`.
2. Require the owner or the approved release group as a deployment reviewer; do not permit the implementer’s alternate identity to satisfy this review.
3. Do not add broad wait timers, bypass actors, or a repository-level secret. Store `NPM_TOKEN` only as an environment secret in `npm-production`.
4. Create a least-privilege npm automation token limited to the required organization/package publication scope and the shortest supported lifetime. Never paste its value into a PR, log, Bead, issue, shell history, or evidence file.
5. Verify metadata only: token owner/scope/lifetime and secret presence are recorded as redacted facts, never as token material.

## Controlled rotation order and rollback

First configure and independently verify the replacement in the protected Environment, then run one separately authorized release test. Only after that verification, revoke the old token. If verification fails, remove the replacement secret, keep the old token available only until the owner decides the rollback window is closed, and do not publish.

Rollback of the workflow code is a normal Git revert. Environment protection and token rotation are owner-executed state changes: restore the previously verified secret only through the GitHub UI or approved secret-management path, never through Git.

## Evidence to attach to `claude-s03q.4`

Record the Environment name, reviewer rule, secret location, token scope/lifetime metadata, verification timestamp, release-test result, old-token revocation timestamp, and confirmation that repository-level `NPM_TOKEN` is absent. Record no secret value, token identifier, or private credential.

The E7.3 Bead remains open and blocked solely on these owner actions. No npm publish, unpublish, deprecation, token operation, Environment mutation, or credential disclosure is authorized by this packet.
