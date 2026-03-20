---
name: evernote-cost-tuning
description: |
  Optimize Evernote integration costs and resource usage.
  Use when managing API quotas, reducing storage usage,
  or optimizing upload limits.
  Trigger with phrases like "evernote cost", "evernote quota",
  "evernote limits", "evernote upload".
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Evernote Cost Tuning

## Overview
Optimize resource usage and manage costs in Evernote integrations, focusing on monthly upload quotas, storage efficiency, image compression, and account limit monitoring.

## Prerequisites
- Understanding of Evernote account tiers (Basic: 60MB/mo, Premium: 10GB/mo, Business: 20GB/mo)
- Access to user quota information via `user.accounting`
- Monitoring infrastructure for alerts

## Instructions

### Step 1: Quota Monitoring

Query `userStore.getUser()` to access `user.accounting` which contains `uploadLimit`, `uploaded`, and `uploadLimitEnd`. Calculate remaining quota and percentage used.

```javascript
async function getQuotaStatus(userStore) {
  const user = await userStore.getUser();
  const { uploadLimit, uploaded, uploadLimitEnd } = user.accounting;
  return {
    totalMB: Math.round(uploadLimit / 1024 / 1024),
    usedMB: Math.round(uploaded / 1024 / 1024),
    remainingMB: Math.round((uploadLimit - uploaded) / 1024 / 1024),
    percentUsed: Math.round((uploaded / uploadLimit) * 100),
    resetsAt: new Date(uploadLimitEnd)
  };
}
```

### Step 2: Resource Optimization

Compress images before attaching to notes. Resize large images to a maximum dimension (e.g., 1920px). Convert PNG screenshots to JPEG for smaller file sizes. Skip attaching files that exceed the single-note size limit (25MB for Basic, 200MB for Premium).

```javascript
function estimateNoteSize(content, resources = []) {
  const contentBytes = Buffer.byteLength(content, 'utf8');
  const resourceBytes = resources.reduce((sum, r) => sum + r.data.size, 0);
  return contentBytes + resourceBytes;
}

function canUpload(noteSize, remainingQuota) {
  return noteSize < remainingQuota;
}
```

### Step 3: Efficient Note Creation

Check quota before creating notes with large attachments. Use `findNotesMetadata()` for read operations (zero upload cost). Batch small notes into single notes where appropriate.

### Step 4: Storage Cleanup

Find large notes consuming quota. List notes sorted by content length to identify optimization candidates. Remove unused resources and delete notes in trash to reclaim space.

### Step 5: Quota Alerts

Send alerts when upload usage exceeds thresholds (e.g., 75%, 90%, 95%). Log quota status after each upload operation for trend analysis.

For the complete quota monitor, image optimizer, cleanup utilities, and alert system, see [Implementation Guide](references/implementation-guide.md).

## Account Limits Reference

| Limit | Basic | Premium | Business |
|-------|-------|---------|----------|
| Monthly upload | 60 MB | 10 GB | 20 GB/user |
| Single note size | 25 MB | 200 MB | 200 MB |
| Notebooks | 250 | 250 | 10,000 |
| Tags | 100,000 | 100,000 | 100,000 |
| Notes | 100,000 | 100,000 | 500,000 |

## Output
- Quota monitoring service with percentage tracking
- Image compression pipeline for resource optimization
- Pre-upload quota check with size estimation
- Storage cleanup utilities for large notes
- Threshold-based alert system for quota usage

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| `QUOTA_REACHED` | Monthly upload limit exceeded | Wait for quota reset at `uploadLimitEnd` |
| `LIMIT_REACHED` | Too many notebooks or tags | Delete unused notebooks, merge duplicate tags |
| `DATA_REQUIRED` | Empty note after optimization | Ensure note still has content after compression |
| `BAD_DATA_FORMAT` | Attachment hash mismatch | Recompute MD5 hash after image compression |

## Resources
- [Account Limits](https://help.evernote.com/hc/articles/209005247)
- [Rate Limits](https://dev.evernote.com/doc/articles/rate_limits.php)
- [API Reference - User.accounting](https://dev.evernote.com/doc/reference/)

## Next Steps
For architecture patterns, see `evernote-reference-architecture`.

## Examples

**Quota dashboard**: Build a dashboard showing current upload usage (MB used / total), days until reset, largest notes by size, and projected usage based on recent trends.

**Image pipeline**: Before attaching images, resize to max 1920px width, convert PNG to JPEG at 80% quality, check resulting size against remaining quota, and skip if insufficient.
