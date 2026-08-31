---
name: grammarly-migration-deep-dive
description: 'Deep dive into Grammarly API migration patterns.

  Use when migrating between API versions or from deprecated endpoints.

  Trigger with phrases like "grammarly migration deep dive",

  "grammarly api migration", "grammarly version change".

  '
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(git:*)
version: 1.8.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- grammarly
- writing
compatibility: Designed for Claude Code
---
# Grammarly Migration Deep Dive

## Overview

The Grammarly Text Editor SDK was deprecated January 2024. Current APIs are Writing Score (v2), AI Detection (v1), and Plagiarism Detection (v1). This skill covers migrating from the deprecated SDK to the current REST APIs.

## Migration: Text Editor SDK to REST APIs

### Before (Deprecated SDK)

```html
<!-- The deprecated approach embedded Grammarly in text editors -->
<script src="https://cdn.grammarly.com/grammarly-sdk.js"></script>
<grammarly-editor-plugin client-id="YOUR_ID">
  <textarea></textarea>
</grammarly-editor-plugin>
```

### After (Current REST APIs)

```typescript
// Server-side scoring replaces client-side editor integration
async function scoreContent(text: string) {
  const token = await getAccessToken();
  const response = await fetch('https://api.grammarly.com/ecosystem/api/v2/scores', {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
    body: JSON.stringify({ text }),
  });
  return response.json();
}
```

## Key Differences

| Feature | Deprecated SDK | Current API |
|---------|---------------|-------------|
| Execution | Client-side | Server-side |
| Real-time suggestions | Yes | No |
| Writing scores | No | Yes |
| AI detection | No | Yes |
| Plagiarism detection | No | Yes |

## Prerequisites

- A signed migration plan with data owners, consent/retention authority, target allowlist, and cutover/rollback owner.
- An inventory of opaque record IDs and aggregate counts rather than exported text, suggestions, or user data.
- A sandbox rehearsal and a proven way to freeze submissions, disable the new integration, and restore the prior path.

## Instructions

1. Baseline aggregate volume, authorization/consent, retention, and synthetic behavior before migrating.
2. Rehearse a bounded idempotent migration in sandbox; quarantine schema, consent, or destination mismatches.
3. Migrate one cohort at a time, compare counts and policy probes, and log opaque correlation IDs only.
4. Cut over after owner approval and an observation window; retain the prior path until recovery criteria are met.
5. Roll back for policy, integrity, retention, or behavior failure and document the failed boundary before retrying.

## Output

Create a migration receipt with cohort, baseline/target counts, consent/retention results, checkpoint, owner approval, cutover status, and rollback reference. Never attach text or credentials.

## Error Handling

Stop on unknown consent, destination, incomplete deletion, non-idempotent replay, or retention drift. Preserve a redacted receipt and restore the prior controlled path rather than forcing the cutover.

## Examples

`cohort=synthetic-editor-01; baseline=420; migrated=420; consent=pass; retention=none; cutover=held; rollback=old-client-r8` documents a safe rehearsal.

## Resources

- [Text Editor SDK Deprecation](https://www.grammarly.com/blog/company/general-availability-grammarly-text-editor-sdk/)
- [Current APIs](https://developer.grammarly.com/)
