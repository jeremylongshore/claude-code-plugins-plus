---
name: customerio-upgrade-migration
description: |
  Manage Customer.io SDK upgrades.
  Use when upgrading SDK versions, migrating integrations,
  or updating to new API versions.
  Trigger with phrases like "upgrade customer.io", "customer.io migration",
  "update customer.io sdk", "customer.io version".
allowed-tools: Read, Grep, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Customer.io Upgrade & Migration

## Current State
!`npm list 2>/dev/null | head -20`
!`pip freeze 2>/dev/null | head -20`

## Overview
Plan and execute Customer.io SDK upgrades and migrations safely with staged rollouts, feature flags, and rollback procedures.

## Prerequisites
- Current SDK version identified
- Test environment available
- Rollback plan prepared

## Instructions

### Assess current configuration
Run version assessment scripts to identify installed SDK versions for Node.js and Python, and check for latest available versions.

### Step 2: Review Breaking Changes
Review the Customer.io changelog for breaking changes between your current and target versions (ESM modules, region config, event data structure changes).

### Step 3: Create Migration Plan
Document current version, target version, breaking changes, required code changes, test cases, rollback procedure, and timeline.

### Step 4: Update Dependencies
Install the target SDK version. Use exact version pinning for production.

### Step 5: Update Code for Breaking Changes
Apply code changes for the new API (e.g., legacy `CustomerIO` to `TrackClient`, positional args to object params).

### Step 6: Write Migration Tests
Create a test suite that validates identify, track, and error handling with the new SDK version.

### Step 7: Implement Staged Rollout
Use feature flags with hash-based percentage rollout to gradually shift traffic from legacy to new SDK.

### Step 8: Run Post-Migration Verification
Verify new SDK is installed, all tests pass, error rates are stable, and delivery metrics are normal.

For detailed code examples and migration scripts, load the reference guide:
`Read(${CLAUDE_SKILL_DIR}/references/implementation-guide.md)`

## Migration Checklist
- [ ] Current version documented
- [ ] Breaking changes reviewed
- [ ] Code changes identified and implemented
- [ ] Migration tests passing
- [ ] Staging deployment successful
- [ ] Staged rollout plan ready
- [ ] Rollback procedure tested
- [ ] Team notified

## Error Handling
| Issue | Solution |
|-------|----------|
| Breaking change missed | Revert and add to change list |
| Performance regression | Profile and optimize or rollback |
| Unexpected errors | Check if error types changed |

## Resources
- [Customer.io Changelog](https://customer.io/docs/changelog/)
- [SDK GitHub Releases](https://github.com/customerio/customerio-node/releases)

## Next Steps
After successful migration, proceed to `customerio-ci-integration` for CI/CD setup.

## Output

- Configuration files or code changes applied to the project
- Validation report confirming correct implementation
- Summary of changes made and their rationale

See [migration implementation details](${CLAUDE_SKILL_DIR}/references/implementation.md) for output format specifications.

## Examples

**Basic usage**: Apply customerio upgrade migration to a standard project setup with default configuration options.

**Advanced scenario**: Customize customerio upgrade migration for production environments with multiple constraints and team-specific requirements.