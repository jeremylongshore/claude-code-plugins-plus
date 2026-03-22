---
name: grammarly-migration-deep-dive
description: |
  Deep dive into Grammarly API migration patterns.
  Use when migrating between API versions or from deprecated endpoints.
  Trigger with phrases like "grammarly migration deep dive",
  "grammarly api migration", "grammarly version change".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(git:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, grammarly, writing]
compatible-with: claude-code
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

## Resources

- [Text Editor SDK Deprecation](https://www.grammarly.com/blog/company/general-availability-grammarly-text-editor-sdk/)
- [Current APIs](https://developer.grammarly.com/)
