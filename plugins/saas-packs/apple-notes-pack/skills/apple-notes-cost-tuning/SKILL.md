---
name: apple-notes-cost-tuning
description: |
  Apple Notes cost optimization — it is free, focus on iCloud storage management.
  Trigger: "apple notes cost".
allowed-tools: Read, Write, Edit, Bash(osascript:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, macos, apple-notes, automation]
compatible-with: claude-code
---

# Apple Notes Cost Tuning

## Overview

Apple Notes itself is free with every Apple ID. The only real cost is iCloud storage, which is shared across Photos, iCloud Drive, Mail, Notes, and device backups. For automation workflows, the main cost drivers are large embedded attachments (images, PDFs, scans) that inflate iCloud usage, and the "On My Mac" account that uses local disk instead. Understanding what consumes storage lets you keep notes within the free 5 GB tier or choose the right iCloud+ plan for your organization.

## iCloud Storage Tiers

| Plan | Storage | Price/mo | Approx Notes Capacity |
|------|---------|----------|----------------------|
| Free | 5 GB | $0 | ~50,000 text-only notes |
| iCloud+ 50 GB | 50 GB | $0.99 | Unlimited text; moderate attachments |
| iCloud+ 200 GB | 200 GB | $2.99 | Shared with Family Sharing |
| iCloud+ 2 TB | 2 TB | $9.99 | Enterprise/heavy media |
| iCloud+ 6 TB | 6 TB | $29.99 | Large teams with shared albums + notes |
| iCloud+ 12 TB | 12 TB | $59.99 | Maximum tier |

## Storage Audit Script

```bash
#!/bin/bash
# Audit Apple Notes storage consumption
echo "=== iCloud Storage Overview ==="
# Total iCloud usage (approximate from system)
df -h ~/Library/Mobile\ Documents/ 2>/dev/null | tail -1

echo ""
echo "=== Notes Content Audit ==="
osascript -l JavaScript -e '
  const Notes = Application("Notes");
  const accounts = Notes.accounts();
  let report = [];
  accounts.forEach(a => {
    const notes = a.notes();
    let totalChars = 0;
    let withAttachments = 0;
    notes.forEach(n => {
      totalChars += n.body().length;
      if (n.attachments().length > 0) withAttachments++;
    });
    report.push(a.name() + ": " + notes.length + " notes, ~" +
      Math.round(totalChars / 1024) + "KB text, " +
      withAttachments + " with attachments");
  });
  report.join("\n");
'
```

## Optimization Strategies

### Move Large Notes to "On My Mac"

```javascript
// Move attachment-heavy notes to local account (no iCloud cost)
const Notes = Application("Notes");
const localAccount = Notes.accounts().find(a => a.name() === "On My Mac");
const icloud = Notes.defaultAccount;

// Find notes with large bodies (likely have embedded images)
const largeNotes = icloud.notes().filter(n => n.body().length > 100000);
largeNotes.forEach(n => {
  console.log(`Large note: ${n.name()} (${Math.round(n.body().length / 1024)}KB)`);
});
// Manual move: drag notes to "On My Mac" in Notes.app sidebar
```

### Archive Old Notes to Markdown

```bash
# Export old notes to local markdown files, then delete from iCloud
ARCHIVE_DIR="$HOME/notes-archive/$(date +%Y-%m)"
mkdir -p "$ARCHIVE_DIR"
osascript -l JavaScript -e '
  const Notes = Application("Notes");
  const cutoff = new Date(Date.now() - 180 * 24 * 60 * 60 * 1000); // 6 months ago
  Notes.defaultAccount.notes()
    .filter(n => n.modificationDate() < cutoff)
    .map(n => JSON.stringify({ title: n.name(), body: n.body() }))
    .join("\n");
' | while IFS= read -r line; do
  title=$(echo "$line" | jq -r '.title' 2>/dev/null) || continue
  safe=$(echo "$title" | tr '/:*?"<>|' '-' | head -c 80)
  echo "$line" | jq -r '.body' > "$ARCHIVE_DIR/$safe.html"
done
echo "Archived to $ARCHIVE_DIR — review before deleting from Notes"
```

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| iCloud storage full | Attachments in Notes + Photos + Backups | Audit per-app usage in System Settings > Apple ID > iCloud |
| "On My Mac" account missing | Disabled in Notes preferences | Notes > Settings > enable "On My Mac" account |
| Notes sync paused | Storage quota exceeded | Delete large attachments or upgrade iCloud plan |
| Cannot determine note sizes | JXA body() returns HTML, not raw bytes | Estimate: HTML chars x 1.5 for actual storage with formatting |

## Resources

- [iCloud+ Plans and Pricing](https://support.apple.com/en-us/108047)
- [Manage iCloud Storage](https://support.apple.com/en-us/105078)
- [Mac Automation Scripting Guide](https://developer.apple.com/library/archive/documentation/LanguagesUtilities/Conceptual/MacAutomationScriptingGuide/)

## Next Steps

For monitoring iCloud sync health, see `apple-notes-observability`. For archiving and data export, see `apple-notes-data-handling`.
