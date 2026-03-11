---
name: granola-local-dev-loop
description: |
  Integrate Granola meeting notes into your local development workflow.
  Use when setting up development workflows, accessing notes programmatically,
  or syncing meeting outcomes with project tools.
  Trigger with phrases like "granola dev workflow", "granola development",
  "granola local setup", "granola developer", "granola coding workflow".
allowed-tools: Read, Write, Edit, Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Granola Local Dev Loop

## Overview
Integrate Granola meeting notes into your local development workflow for seamless project management.

## Prerequisites
- Granola installed and configured
- Zapier account (for automation)
- Project management tool (Jira, Linear, GitHub Issues)
- Local development environment

## Instructions

### Step 1: Export Notes Workflow
Configure automatic export of meeting notes:

1. Open Granola Settings
2. Go to Integrations > Zapier
3. Connect your Zapier account
4. Create a Zap: "New Granola Note" trigger

### Step 2: Set Up Local Sync
Create a local directory for meeting notes:

```bash
# Create meeting notes directory
mkdir -p ~/dev/meeting-notes

# Create sync script
cat > ~/dev/scripts/sync-granola-notes.sh << 'EOF'
#!/bin/bash
# Sync Granola notes to local project

NOTES_DIR="$HOME/dev/meeting-notes"
PROJECT_DIR="$1"

if [ -z "$PROJECT_DIR" ]; then
    echo "Usage: sync-granola-notes.sh <project-dir>"
    exit 1
fi

# Copy relevant notes to project docs
cp -r "$NOTES_DIR"/*.md "$PROJECT_DIR/docs/meetings/" 2>/dev/null

echo "Synced meeting notes to $PROJECT_DIR/docs/meetings/"
EOF

chmod +x ~/dev/scripts/sync-granola-notes.sh
```

### Step 3: Integrate with Git Workflow
```bash
# Add meeting notes to .gitignore if sensitive
echo "docs/meetings/*.md" >> .gitignore

# Or track action items only
cat > docs/meetings/README.md << 'EOF'
# Meeting Notes

Action items and decisions from team meetings.
Full notes available in Granola app.
EOF
```

### Step 4: Create Action Item Extractor
```python
#!/usr/bin/env python3
# extract_action_items.py

import re
import sys

def extract_actions(note_file):
    with open(note_file, 'r') as f:
        content = f.read()

    # Find action items section
    actions = re.findall(r'- \[ \] (.+)', content)

    for action in actions:
        print(f"TODO: {action}")

if __name__ == "__main__":
    extract_actions(sys.argv[1])
```

## Output
- Local meeting notes directory structure
- Sync script for project integration
- Action item extraction workflow
- Git-integrated note tracking

## Workflow Example
```
1. Attend sprint planning meeting
   Granola captures notes automatically

2. Notes sync to local directory
   ~/dev/meeting-notes/2025-01-06-sprint-planning.md  # 2025 year

3. Extract action items
   python extract_action_items.py notes/sprint-planning.md

4. Create tickets automatically
   ./create-tickets.sh TODO.md

5. Reference in commits
   git commit -m "feat: implement login - per meeting 2025-01-06"
```

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| Sync Failed | Zapier disconnected | Reconnect Zapier integration |
| Notes Not Appearing | Export delay | Wait 2-5 minutes after meeting |
| Parsing Errors | Note format changed | Update extraction regex |
| Permission Denied | Directory access | Check file permissions |

## Resources
- [Granola Zapier Integration](https://granola.ai/integrations/zapier)
- [Granola Export Formats](https://granola.ai/help/export)

## Next Steps
Proceed to `granola-sdk-patterns` for advanced Zapier automation patterns.

## Examples

**Basic usage**: Apply granola local dev loop to a standard project setup with default configuration options.

**Advanced scenario**: Customize granola local dev loop for production environments with multiple constraints and team-specific requirements.