# Granola Migration Deep Dive - Implementation Details

## Source-Specific Export Procedures

### From Otter.ai
1. Log into Otter.ai
2. Go to each conversation > ... menu > Export (TXT/PDF/SRT)
3. Bulk Export (Pro/Business): Settings > My Account > Export All > Wait for email

### From Fireflies.ai
1. Log in > Meetings > Select meetings > Export > Choose JSON
2. API Export (Enterprise): `curl -X GET "https://api.fireflies.ai/v1/transcripts" -H "Authorization: Bearer $FIREFLIES_API_KEY"`

### From Fathom
1. Open dashboard > Select call > Download (Markdown/CSV)
2. Contact support for bulk export

### From Zoom/Meet/Teams
- Zoom: Web portal > Recordings > Download VTT transcript
- Google Meet: Check Drive for meeting recordings folder
- Teams: Download VTT from meeting recording

## Data Mapping

```yaml
# Otter.ai -> Granola
conversation_title -> meeting_title
date -> meeting_date
transcript -> transcript
summary -> summary
action_items -> action_items
speakers -> attendees (partial)

# Fireflies -> Granola
title -> meeting_title
transcript -> transcript
summary -> summary
participants -> attendees
```

## Conversion Scripts

### Otter.ai Converter
```python
#!/usr/bin/env python3
import json, os
from datetime import datetime

def convert_otter_to_granola(otter_file, output_dir):
    with open(otter_file, 'r') as f:
        content = f.read()

    granola_note = f"""# Meeting Notes
**Imported from:** Otter.ai
**Original Date:** {datetime.now().strftime('%Y-%m-%d')}

## Transcript
{content}

## Action Items
[Review and extract manually]

---
*Migrated to Granola on {datetime.now().strftime('%Y-%m-%d')}*
"""
    output_file = os.path.join(output_dir, 'imported_note.md')
    with open(output_file, 'w') as f:
        f.write(granola_note)
    return output_file
```

### Batch Converter
```python
#!/usr/bin/env python3
from pathlib import Path

def batch_convert(source_dir, output_dir, source_type):
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    converters = { 'otter': convert_otter, 'fireflies': convert_fireflies, 'zoom': convert_zoom_vtt }
    converter = converters.get(source_type)
    if not converter:
        raise ValueError(f"Unknown source type: {source_type}")

    converted = []
    for file in Path(source_dir).glob('*'):
        try:
            output = converter(file, output_dir)
            converted.append(output)
        except Exception as e:
            print(f"Error converting {file.name}: {e}")
    print(f"\nConverted {len(converted)} files")
```

## Execution Plan

### Week 1: Preparation
- Day 1-2: Inventory data, identify critical meetings, document integrations
- Day 3-4: Export from source, verify completeness, secure backups
- Day 5: Configure Granola workspace, set up integrations, test with sample

### Week 2: Migration
- Day 1-2: Run conversion scripts, validate data, fix errors
- Day 3-4: Import to external archive (Notion), tag as historical
- Day 5: Spot check samples, verify search, document locations

### Week 3-4: Parallel Running
- Record in Granola (primary), source tool as backup
- Compare quality daily, gather feedback
- End of parallel: review comparison, get sign-off, schedule cutover

### Week 5: Cutover
- Day 1: Final export and conversion from source
- Day 2: Disable source tool, cancel subscription
- Day 3-5: Monitor closely, address issues immediately

## Communication Templates

### Announcement
```
Subject: Switching to Granola for Meeting Notes

Key Dates:
- Parallel running: [Start] - [End]
- Full cutover: [Date]

What You Need to Do:
1. Install Granola: granola.ai/download
2. Sign in with company SSO
3. Attend training: [Date/Link]
```

### Training Agenda (30 min)
1. Introduction - Why Granola (5 min)
2. Setup - Install, connect calendar (10 min)
3. First Meeting - Recording, notes, review (10 min)
4. Q&A (5 min)

## Rollback Plan
Triggers: >20% meetings not captured, critical integration failure, adoption <30%, data loss detected.

Steps: Communicate pause, re-enable source tool, export Granola notes, investigate, remediate, retry.

## Post-Migration Success Metrics (30-Day Review)
- Active users: ___% of total
- Meetings captured: ___/week
- User satisfaction: ___/5
- Open tickets: ___, Resolved: ___
