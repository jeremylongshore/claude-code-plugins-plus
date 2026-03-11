# Granola Incident Runbook - Implementation Details

## Quick Status Check

```bash
# Check Granola status page
curl -s https://status.granola.ai/api/v2/status.json | jq '.status'

# Test API connectivity
curl -I https://api.granola.ai/health

# macOS - Check if Granola is running
pgrep -l Granola

# Check Granola logs
tail -f ~/Library/Logs/Granola/granola.log
```

## Incident: Recording Not Starting

### Quick Fix (< 5 min)
1. Manually click "Start Recording" in Granola
2. Check calendar is connected (Settings > Integrations)
3. Verify meeting is on synced calendar
4. Restart Granola app
5. Check audio permissions granted

### Root Cause Investigation
- Calendar Sync: Last sync time? OAuth token valid? Correct calendar selected?
- Audio Permission: System Preferences > Security > Microphone - Is Granola listed?
- App State: Force quit and restart, clear cache, check for updates

## Incident: No Audio Captured

### Quick Fix
1. Check audio input device in System Preferences
2. Verify physical mic is not muted
3. Test mic with other app (Voice Memos)
4. Restart Granola app
5. Rejoin meeting if possible

### Workaround
Take manual notes, record with backup tool (QuickTime, OBS), upload/transcribe after meeting.

## Incident: Processing Stuck

### Quick Fix
1. Wait up to 15 minutes (large meetings take longer)
2. Check internet connectivity
3. Check status page for delays
4. Restart Granola app
5. Contact support if > 20 min

### Support Escalation
Email: help@granola.ai
Include: meeting date/time, meeting ID, duration, error messages, steps tried.

## Incident: Integration Failure

### Quick Fix
1. Check integration status (Settings > Integrations)
2. Reconnect if showing "Disconnected"
3. Test integration manually
4. Check destination app permissions
5. Verify Zapier Zap is enabled

### Manual Workaround
Export note as Markdown. Manually paste to Notion/Slack. Create tasks manually in Linear.

## Incident: Complete Outage

### During Outage
1. Acknowledge internally (Slack)
2. Enable backup note-taking
3. Monitor status page
4. Document affected meetings

### Backup Procedures
Designate note-taker per meeting, use Google Docs/Notion directly, record via native platform recording.

## Communication Templates

### Internal (Slack)
```
:warning: Granola Incident
Status: [Investigating/Identified/Monitoring/Resolved]
Impact: [Description]
Workaround: [Available workaround]
ETA: [Expected resolution]
Next update: [Time]
```

### User Notification (Email)
```
Subject: Granola Service Update
We're aware of issues with [issue] affecting [scope].
Impact: [What users experience]
Workaround: [Steps users can take]
We'll update within [timeframe].
```

## Post-Incident Report Template
```markdown
## Incident Report: [Title]
**Date:** [Date/Time]  **Duration:** [Start to resolution]
**Severity:** [P1/P2/P3/P4]  **Impact:** [Users/meetings affected]

**Timeline:**
- HH:MM - Incident detected
- HH:MM - Investigation started
- HH:MM - Root cause identified
- HH:MM - Resolution applied

**Root Cause:** [Description]
**Resolution:** [What was done]
**Prevention:** [Steps to prevent recurrence]
```

## Escalation Path
1. Primary: IT Support
2. Secondary: Granola Admin
3. Management: Team Lead
4. Executive: VP/CTO (P1 only)
