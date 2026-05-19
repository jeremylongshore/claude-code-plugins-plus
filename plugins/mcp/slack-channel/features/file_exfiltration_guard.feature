# SPDX-License-Identifier: MIT
# Feature owner: engineer. AI tooling may add glue (step definitions,
# runners) but MUST NOT edit the scenarios below. See features/README.md.
#
# Primitive: assertSendable() in lib.ts — outbound file-upload guard.
# Anchor: "Pure, testable functions extracted from the Slack Channel MCP server."

Feature: Outbound file exfiltration guard
  The file-send guard is the defense that stands between Claude and
  the credential store. Every call to chat.uploadFile or
  files.upload runs its path through this guard first. The guard
  rejects traversal components, paths outside the allowlisted roots,
  credentials identified by basename, and paths that descend through
  known-sensitive parent directories. A path that clears the guard
  is considered safe to upload to Slack; a path that fails is never
  opened for read.

  Background:
    Given an inbox directory exists at a known location
    And the allowlisted sendable roots are configured explicitly
    And the state root contains credential files that are never sendable

  Scenario: A traversal path with a parent-directory component is rejected
    When a caller requests a file path that contains a parent-component token
    Then the guard throws before consulting the filesystem
    And the error message names the traversal check

  Scenario: A path that does not resolve on the filesystem is rejected
    When a caller requests a path that realpath cannot resolve
    Then the guard throws with an access error
    And no symlink is followed against the allowlist

  Scenario: A file inside the state directory but outside the inbox is rejected
    When a caller requests a path that resolves under the state root
    Then the guard throws because the state root is blanket-denied
    And the inbox carve-out does not apply

  Scenario: A file inside the inbox under the state root is accepted
    When a caller requests a path that resolves under the inbox directory
    Then the guard allows the upload
    And the inbox carve-out supersedes the state-root block

  Scenario: A credential file matched by basename is rejected even under an allowlisted root
    Given a credential file lives under an allowlisted root
    When a caller requests that credential file by path
    Then the guard throws because the basename matches the credential denylist

  Scenario: A path descending through a sensitive single-component directory is rejected
    When a caller requests a file whose parent chain includes a sensitive directory name
    Then the guard throws because the component denylist applies

  Scenario: A path descending through a sensitive adjacent-pair directory is rejected
    When a caller requests a file whose parent chain matches a pair denylist entry
    Then the guard throws because an adjacent-pair match applies

  Scenario: A path outside every allowlisted root and outside the inbox is rejected
    When a caller requests a path that resolves outside the configured roots
    Then the guard throws because the allowlist does not cover the location
