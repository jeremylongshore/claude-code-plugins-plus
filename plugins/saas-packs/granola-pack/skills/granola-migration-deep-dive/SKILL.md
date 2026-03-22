---
name: granola-migration-deep-dive
description: |
  Migrate to Granola from Otter.ai, Fireflies, Fathom, tl;dv, or manual note-taking.
  Covers data export from source tools, parallel-run strategy, team transition,
  and historical data preservation.
  Trigger: "migrate to granola", "switch to granola", "granola from otter",
  "granola from fireflies", "replace meeting tool with granola".
allowed-tools: Read, Write, Edit, Bash(python3:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, granola, migration]

---
# Granola Migration Deep Dive

## Overview
Comprehensive guide for migrating to Granola from competing meeting note tools. Covers source-specific export procedures, historical data preservation, parallel-run strategy, team transition, and cutover execution. Granola's key differentiator — no bot joins meetings — means the migration also changes the user experience fundamentally.

## Prerequisites
- Access to source tool with export capability
- Granola workspace configured (see `granola-install-auth`)
- Migration timeline agreed with stakeholders
- Budget approved for Granola licenses

## Instructions

### Step 1 — Assess Migration Scope

```markdown
## Migration Assessment

Source tool: [Otter.ai / Fireflies / Fathom / tl;dv / Manual / Other]
Total meetings in source: [____]
Date range: [____] to [____]
Active users to migrate: [____]
Integrations to recreate: [Slack, Notion, CRM, etc.]
Historical data priority: [Archive all / Selective / Fresh start]
Target cutover date: [____]
Parallel run duration: [1 week / 2 weeks]
```

### Step 2 — Source-Specific Export

#### From Otter.ai
- **Export format:** TXT, SRT (subtitles), PDF
- **Bulk export:** Otter Pro/Business: Settings > Export > Download All
- **Limitations:** Free plan only exports individual notes
- **Key data:** Transcripts with timestamps, speaker labels, action items

#### From Fireflies.ai
- **Export format:** TXT, JSON, PDF, SRT
- **Bulk export:** Admin > Data Management > Export
- **Limitations:** Custom fields may not export
- **Key data:** Transcripts, AI summaries, custom topics

#### From Fathom
- **Export format:** Markdown, CSV, video clips
- **Bulk export:** Settings > Data > Export All
- **Limitations:** Video clips don't transfer
- **Key data:** Meeting summaries, action items, highlights

#### From tl;dv
- **Export format:** TXT, video recordings
- **Bulk export:** Settings > Data Export
- **Limitations:** AI highlights may not transfer
- **Key data:** Transcripts, timestamps, meeting recordings

#### From Manual Notes (Google Docs, Notion, Confluence)
- Already in accessible format
- No export needed — archive in place
- Focus on establishing the Granola workflow going forward

### Step 3 — Choose Migration Strategy

| Strategy | When to Use | Data Handling | Effort |
|----------|------------|--------------|--------|
| **Fresh Start** | <100 historical meetings, or meetings have low reference value | Archive source data externally, start fresh in Granola | Low |
| **Selective Migration** | 100-1000 meetings, some have ongoing reference value | Export key meetings (client calls, decisions, contracts) | Medium |
| **Full Archive** | Enterprise with compliance requirements, everything must be searchable | Export all data, archive in Notion/Drive/cloud storage | High |

**Recommended for most teams:** Fresh Start or Selective. Granola doesn't import historical data from other tools — there's no import feature. Historical data lives in your archive (Notion, Google Drive, local files).

### Step 4 — Archive Historical Data

For important historical meetings, archive before cutting over:

```python
#!/usr/bin/env python3
"""Organize exported meeting notes for archival."""
import os
from pathlib import Path

EXPORT_DIR = Path("~/Downloads/otter-export").expanduser()  # Adjust for your source
ARCHIVE_DIR = Path("~/Documents/meeting-archive").expanduser()

# Create organized archive structure
categories = {
    "client": ["client", "customer", "deal", "sales", "demo"],
    "engineering": ["sprint", "standup", "architecture", "review", "retro"],
    "product": ["product", "prd", "design", "feedback", "roadmap"],
    "leadership": ["all-hands", "board", "strategy", "planning"],
    "general": [],  # catch-all
}

ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
for cat in categories:
    (ARCHIVE_DIR / cat).mkdir(exist_ok=True)

for file in EXPORT_DIR.glob("*.txt"):
    filename_lower = file.name.lower()
    placed = False
    for cat, keywords in categories.items():
        if any(kw in filename_lower for kw in keywords):
            dest = ARCHIVE_DIR / cat / file.name
            file.rename(dest)
            placed = True
            break
    if not placed:
        (ARCHIVE_DIR / "general" / file.name).rename(file)

print(f"Archived to {ARCHIVE_DIR}")
```

Alternatively, upload the archive to Notion or Google Drive for team-wide searchability.

### Step 5 — Parallel Run (2 Weeks)

Run both tools simultaneously to build confidence:

**Week 1: Dual recording**
- Keep source tool active (bot still joins or captures)
- Enable Granola on all meetings (system audio capture)
- Compare output quality daily:

| Metric | Source Tool | Granola | Winner |
|--------|-----------|---------|--------|
| Transcription accuracy | ___% | ___% | |
| Action item detection | ___/total | ___/total | |
| Summary quality | ___/5 | ___/5 | |
| Processing time | ___ min | ___ min | |
| User experience (no bot) | N/A | Yes | Granola |

**Week 2: Granola primary**
- Keep source tool as backup only (disable auto-record if possible)
- All sharing and distribution via Granola integrations
- Team members report any quality issues

### Step 6 — Cutover Execution

**Cutover day checklist:**
- [ ] Final export from source tool (last day of data)
- [ ] Verify archive is complete and accessible
- [ ] Disable source tool recording/bot
- [ ] Remove source tool bot from calendar (if applicable)
- [ ] Cancel source tool subscription (save on unused billing)
- [ ] Announce to team via email/Slack:

```markdown
Subject: Meeting Notes Migration Complete — Granola is Now Primary

Team,

As of today, we've completed our migration to Granola for meeting notes.

What's changed:
- No more [Otter/Fireflies/etc.] bot joining meetings
- Granola captures audio directly from your device (no bot visible to participants)
- Notes are auto-enhanced with AI summaries and action items

What you need to do:
1. Ensure Granola is running on your device
2. Verify your calendar is connected (Settings > Calendar)
3. Check that microphone + Screen & System Audio permissions are granted

Historical notes: Archived at [Notion link / Drive folder]
Support: Post in #granola-support

Thank you for the smooth transition!
```

- [ ] Monitor for 3 days:
  - Capture rate (% of meetings recorded)
  - Support ticket volume
  - User feedback
  - Integration sync health

### Step 7 — Post-Migration Optimization

After 1 week on Granola exclusively:
- [ ] Configure templates for each meeting type (see `granola-core-workflow-a`)
- [ ] Set up Zapier automation for recurring workflows
- [ ] Create custom recipes for team-specific post-meeting tasks
- [ ] Establish folder structure matching team workflow
- [ ] Delete source tool accounts and data (if no longer needed)

## Key Differences from Bot-Based Tools

| Feature | Bot-Based (Otter, Fireflies, tl;dv) | Granola |
|---------|--------------------------------------|---------|
| Meeting join | Bot joins as participant | No bot — system audio capture |
| Participant awareness | "Bot is recording" banner | No banner (still announce recording for consent) |
| Platform support | Platform-specific integrations | Any platform (captures system audio) |
| Typed notes | Separate app | Built-in notepad merges with transcript |
| Enhancement | Auto-generated | User-controlled (click Enhance) |
| Templates | Limited | 29 built-in + custom |
| Chat | Limited or none | Full Granola Chat with Recipes |
| Built-in CRM | No | People & Companies |

## Output
- Source data exported and archived
- Parallel run completed with quality validation
- Team migrated and recording in Granola
- Source tool deactivated and subscription cancelled
- Historical data accessible in archive

## Error Handling

| Error | Cause | Fix |
|-------|-------|-----|
| Source export incomplete | Free plan limits bulk export | Upgrade source plan temporarily for export, then cancel |
| Team resistance to change | Comfort with existing tool | Share quality comparison data from parallel run |
| Missing historical context | No import feature in Granola | Point team to archived data (Notion/Drive) |
| Audio quality different than bot | System audio vs. platform API | Optimize audio setup (see `granola-performance-tuning`) |
| Low adoption post-migration | Setup issues | Run drop-in support sessions, share quick-start guide |

## Resources
- [Granola Setup Guide](https://docs.granola.ai/help-center/getting-started/setting-up-granola-for-the-first-time)
- [Granola vs Otter Comparison](https://www.granola.ai/compare)
- [Granola Free Trial](https://www.granola.ai/blog/granola-free-trial-get-started)
- [Granola for Sales Teams](https://www.granola.ai/blog/sales-ai-notetaker-integration-guide-salesforce-hubspot)

## Next Steps
After migration, explore `granola-performance-tuning` to optimize output quality.
