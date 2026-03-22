---
name: granola-data-handling
description: |
  Manage Granola data export, retention policies, GDPR/CCPA compliance,
  and archival workflows. Handle Subject Access Requests and Right to Erasure.
  Trigger: "granola export", "granola data", "granola GDPR",
  "granola retention", "granola delete data", "granola compliance".
allowed-tools: Read, Write, Edit, Bash(python3:*), Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, granola, compliance, data, gdpr]

---
# Granola Data Handling

## Overview
Manage data lifecycle for Granola meeting data: export, retention policies, GDPR/CCPA compliance, and long-term archival. Covers individual data rights, organizational policies, and automated archival workflows.

## Prerequisites
- Granola admin access (for retention policies)
- Understanding of applicable regulations (GDPR, CCPA, SOC 2)
- Export destination prepared (cloud storage, Notion, local)

## Instructions

### Step 1 — Understand Data Types and Sensitivity

| Data Type | What It Contains | Sensitivity | Storage |
|-----------|-----------------|-------------|---------|
| Meeting Notes | Your typed notes + AI-enhanced output | Medium | Granola cloud + local cache |
| Transcripts | Full text transcription of audio | High (verbatim speech) | Granola cloud + local cache |
| Audio | Raw meeting audio | Critical | **Deleted after transcription** (not stored) |
| Attendee Info | Names, emails from calendar events | PII | Granola cloud (People & Companies) |
| Calendar Metadata | Event titles, times, attendee lists | Low-Medium | Synced from Google/Outlook |

**Key fact:** Granola does **not** store raw audio after transcription. This is a significant privacy advantage — there is no audio file to leak, export, or subpoena.

### Step 2 — Export Meeting Data

**Individual note export:**
1. Open the meeting note in Granola
2. Click the **...** menu > **Copy** (copies as Markdown)
3. Paste into your target: Notion, Google Doc, text editor

**Important limitation:** Granola does **not** currently support bulk export, PDF export, or structured file download (JSON/CSV). The available options are:
- Copy individual notes as text/Markdown
- Share to Notion (one note at a time via native integration)
- Share to Slack (one note at a time)
- Enterprise API (read-only access to workspace notes)

**Workaround for bulk access — local cache:**
```python
#!/usr/bin/env python3
"""Export Granola meetings from local cache to Markdown files."""
import json
from pathlib import Path
from datetime import datetime

CACHE_PATH = Path.home() / "Library/Application Support/Granola/cache-v3.json"
OUTPUT_DIR = Path.home() / "Desktop/granola-export"
OUTPUT_DIR.mkdir(exist_ok=True)

def export_from_cache():
    raw = json.loads(CACHE_PATH.read_text())
    state = json.loads(raw) if isinstance(raw, str) else raw
    data = state.get("state", state)
    docs = data.get("documents", {})

    exported = 0
    for doc_id, doc in docs.items():
        title = doc.get("title", "Untitled").replace("/", "-")
        created = doc.get("created_at", "unknown")[:10]
        content = doc.get("last_viewed_panel", {})

        # Extract text from ProseMirror content (simplified)
        text_parts = []
        if isinstance(content, dict):
            for node in content.get("content", []):
                if node.get("type") == "paragraph":
                    for child in node.get("content", []):
                        text_parts.append(child.get("text", ""))
                elif node.get("type") == "heading":
                    level = node.get("attrs", {}).get("level", 1)
                    prefix = "#" * level
                    for child in node.get("content", []):
                        text_parts.append(f"\n{prefix} {child.get('text', '')}\n")

        filename = f"{created}_{title[:60]}.md"
        filepath = OUTPUT_DIR / filename
        filepath.write_text(f"# {title}\n\nDate: {created}\n\n{''.join(text_parts)}")
        exported += 1

    print(f"Exported {exported} meetings to {OUTPUT_DIR}")

export_from_cache()
```

**Enterprise API export:**
```bash
# List all accessible notes (Enterprise plan required)
curl -s "https://api.granola.ai/v0/notes" \
  -H "Authorization: Bearer $GRANOLA_API_KEY" \
  -H "Content-Type: application/json" | python3 -c "
import json, sys
notes = json.load(sys.stdin).get('notes', [])
for note in notes[:10]:
    print(f\"{note.get('id', 'N/A')}: {note.get('title', 'Untitled')} ({note.get('created_at', 'N/A')})\")
print(f'Total accessible notes: {len(notes)}')
"
```

### Step 3 — Configure Retention Policies

Settings > **Data Retention** (Business/Enterprise):

| Data Type | Recommended Retention | Rationale |
|-----------|----------------------|-----------|
| Meeting notes | 1-2 years | Long-term reference value |
| Transcripts | 90 days | Storage efficiency, lower PII risk |
| Audio | Deleted after processing | Granola default, not configurable |
| Attendee info | Retained with notes | Needed for People & Companies CRM |

**Per-workspace overrides (Enterprise):**
- HR workspace: 90-day notes, 30-day transcripts
- Executive workspace: Custom (legal hold capable)
- Sales workspace: 1-year notes, 90-day transcripts
- Engineering workspace: 2-year notes, 90-day transcripts

### Step 4 — GDPR Compliance

**Required controls:**

| GDPR Right | Granola Implementation |
|-----------|----------------------|
| Right of Access (Art. 15) | Export user's data via Settings > Data > Export or Enterprise API |
| Right to Erasure (Art. 17) | Delete individual notes; request account deletion from Granola |
| Right to Data Portability (Art. 20) | Copy notes as text, or use local cache export |
| Right to Object (Art. 21) | AI training opt-out (Business/Enterprise) |
| Lawful Basis | Consent (recording notice) or Legitimate Interest (employer's business ops) |

**Subject Access Request (SAR) handling:**
```markdown
## SAR Response Procedure

1. Receive SAR from data subject (30-day response deadline)
2. Verify identity of the requester
3. Search Granola for all notes containing the requester
   - People view: search by name/email
   - Enterprise API: query notes by attendee email
4. Export relevant notes (copy as text)
5. Redact third-party PII from the export
6. Deliver export to requester within 30 days
7. Document the SAR and response in compliance log
```

**Data Processing Agreement:**
- Request DPA from Granola at security@granola.ai or via Settings
- Required for any organization processing EU personal data
- DPA covers Granola as a Data Processor

### Step 5 — CCPA Compliance

For California consumer data:
- **Disclosure:** Update your privacy policy to mention Granola as a meeting recording tool
- **Opt-out:** Provide mechanism for meeting participants to opt out of recording
- **Deletion:** Honor deletion requests by removing notes containing the individual

### Step 6 — Archival Workflow

For long-term retention beyond Granola:

```yaml
# Monthly archival via Zapier
Trigger: Schedule by Zapier — 1st of month

Step 1 — Granola: List notes from past month
  (via Enterprise API or folder trigger accumulation)

Step 2 — Google Drive: Create folder
  Name: "Meeting Archives / YYYY-MM"

Step 3 — Google Drive: Upload files
  Content: Note markdown for each meeting

Step 4 — Slack: Notify admin
  Message: "Monthly meeting archive created: X notes archived"
```

**Alternative: local cache backup**
```bash
# Backup local cache monthly
BACKUP_DIR="$HOME/backups/granola"
mkdir -p "$BACKUP_DIR"
cp "$HOME/Library/Application Support/Granola/cache-v3.json" \
   "$BACKUP_DIR/cache-v3-$(date +%Y%m%d).json"
echo "Granola cache backed up"
```

## Output
- Data export procedures documented and tested
- Retention policies configured per workspace and data type
- GDPR/CCPA compliance controls implemented
- SAR handling procedure established
- Archival workflow automated (monthly)

## Error Handling

| Error | Cause | Fix |
|-------|-------|-----|
| Cannot export notes | No bulk export feature | Use local cache export script or Enterprise API |
| SAR deadline at risk | No process owner | Assign dedicated compliance contact |
| Retention policy not applied | Enterprise feature required | Upgrade to Enterprise, or manually manage |
| Archive missing notes | Cache didn't contain all notes | Use Enterprise API for complete workspace data |
| Deletion incomplete | Backup retention period | Allow 30 days for Granola to purge from all backups |

## Resources
- [Privacy & Data FAQs](https://docs.granola.ai/help-center/consent-security-privacy/security-privacy-data-faqs)
- [Data Processing Addendum](https://help.granola.ai/article/data-processing-addendum)
- [Security Standards](https://docs.granola.ai/help-center/consent-security-privacy/our-security-standards)
- [Granola Privacy Policy](https://www.granola.ai/privacy)

## Next Steps
Proceed to `granola-enterprise-rbac` for role-based access control configuration.
