---
description: View the learnings queue without processing
allowed-tools: Bash, Read
---

## Context
- Queue file: per-project at `~/.claude/projects/<encoded-cwd>/learnings-queue.json`
- Legacy global queue (`~/.claude/learnings-queue.json`) is auto-migrated on first access

## Your Task

Display the current learnings queue in a readable format with confidence scores, patterns, and relative timestamps.

**Output format:**
```
════════════════════════════════════════════════════════════
LEARNINGS QUEUE: [N] items
════════════════════════════════════════════════════════════

[0.85] "use gpt-5.1 not gpt-5" (use-X-not-Y) - 2 days ago
[0.70] "perfect, that's exactly right" (positive) - 5 days ago
[0.90] "remember: always run tests" (explicit) - just now

════════════════════════════════════════════════════════════
Commands:
  /reflect        - Process and save learnings
  /skip-reflect   - Discard all learnings
════════════════════════════════════════════════════════════
```

If queue is empty:
```
════════════════════════════════════════════════════════════
LEARNINGS QUEUE: Empty
════════════════════════════════════════════════════════════
No learnings queued. Use "remember: <learning>" to add items,
or corrections will be auto-detected. Run /reflect to process.
════════════════════════════════════════════════════════════
```

## Implementation

**Step 1: Read the project-scoped queue file:**
```bash
python3 scripts/read_queue.py 2>/dev/null || echo "[]"
```

**Step 2: Parse and format each item with:**
- **Confidence score**: `[0.XX]` format, from `item.confidence` (default 0.60 if missing)
- **Message preview**: First 50 chars with "..." if longer, from `item.message`
- **Pattern name**: In parentheses, from `item.patterns` (show first pattern if multiple)
- **Relative timestamp**: Human-readable time difference from `item.timestamp`

**Relative time calculation:**

Calculate the difference between now and `item.timestamp` (ISO 8601 format):
- Less than 1 minute → "just now"
- Less than 1 hour → "X minutes ago"
- Less than 24 hours → "X hours ago"
- Less than 7 days → "X days ago"
- Otherwise → "X weeks ago" or show date

**Python snippet for relative time:**
```python
from datetime import datetime, timezone

def relative_time(iso_timestamp):
    """Convert ISO timestamp to relative time string."""
    try:
        dt = datetime.fromisoformat(iso_timestamp.replace('Z', '+00:00'))
        now = datetime.now(timezone.utc)
        diff = now - dt

        seconds = diff.total_seconds()
        if seconds < 60:
            return "just now"
        elif seconds < 3600:
            minutes = int(seconds / 60)
            return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
        elif seconds < 86400:
            hours = int(seconds / 3600)
            return f"{hours} hour{'s' if hours > 1 else ''} ago"
        elif seconds < 604800:
            days = int(seconds / 86400)
            return f"{days} day{'s' if days > 1 else ''} ago"
        else:
            weeks = int(seconds / 604800)
            return f"{weeks} week{'s' if weeks > 1 else ''} ago"
    except:
        return "unknown"
```

**Formatting rules:**
- Confidence: Always show 2 decimal places `[0.85]`
- Message: Truncate at 50 chars, add "..." if longer
- Patterns: Show in parentheses `(pattern-name)`
- If patterns field is empty, show `(auto)` for auto-detected or `(explicit)` for remember:
- Time: Right-aligned relative timestamp

**Example output line:**
```
[0.85] "use gpt-5.1 not gpt-5" (use-X-not-Y) - 2 days ago
```
