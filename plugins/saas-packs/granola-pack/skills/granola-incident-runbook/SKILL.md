---
name: granola-incident-runbook
description: |
  Incident response procedures for Granola meeting capture failures and outages.
  Use when meetings aren't recording, transcription fails mid-meeting,
  integrations stop syncing, or the Granola service is down.
  Trigger: "granola incident", "granola outage", "granola down",
  "granola not recording", "granola emergency".
allowed-tools: Read, Write, Edit, Bash(curl:*), Bash(pgrep:*), Bash(pkill:*), Bash(open:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, granola, incident-response]

---
# Granola Incident Runbook

## Overview
Standard operating procedures for Granola incidents — from individual recording failures to organization-wide outages. Covers triage, remediation, communication, escalation, and post-incident review. Designed for IT admins, team leads, and individual users.

## Prerequisites
- Granola admin access (for org-level incidents)
- Bookmark [status.granola.ai](https://status.granola.ai) for service status
- Internal communication channel identified (#granola-support or similar)

## Instructions

### Step 1 — Triage: Assess Severity

```bash
# Quick status check
curl -s "https://status.granola.ai/api/v2/status.json" 2>/dev/null | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    indicator = data.get('status', {}).get('indicator', 'unknown')
    desc = data.get('status', {}).get('description', 'Unknown')
    print(f'Status: {indicator} — {desc}')
except:
    print('Cannot reach status page — possible network issue')
" || echo "Network error — check internet connection"
```

| Severity | Description | Response Time | Example |
|----------|-------------|---------------|---------|
| **P1 Critical** | Org-wide outage, data loss risk | Immediate | Granola service down, no one can record |
| **P2 High** | Multiple users affected | < 1 hour | Recording fails for a team, sync broken |
| **P3 Medium** | Single user issue | < 4 hours | One person's transcription stopped |
| **P4 Low** | Minor issue, workaround exists | < 24 hours | UI glitch, slow processing |

**Scope assessment questions:**
1. Is it just you, or are others affected too? → Ask in #granola-support
2. Is [status.granola.ai](https://status.granola.ai) showing an incident? → P1/P2 if yes
3. Was it working earlier today? → Recent change (OS update, permissions) likely
4. Which platform? (Zoom/Meet/Teams) → Platform-specific audio routing

### Step 2 — Remediation by Incident Type

---

#### Incident: "Meeting Not Recording"

**Severity:** P3 (single user) or P2 (team-wide)

**Immediate actions:**
1. Click Granola menu bar icon > **Start Recording** (manual override)
2. If manual start fails:
   - Check that the meeting has audio playing
   - Verify Granola is running: `pgrep -l Granola`
   - Restart: right-click menu bar icon > **Restart Granola**

**Root cause investigation:**
- [ ] Calendar event has a video conferencing link (Zoom/Meet/Teams)
- [ ] Calendar is connected in Settings > Calendar
- [ ] Microphone permission granted
- [ ] Screen & System Audio Recording permission granted (macOS)
- [ ] Not running conflicting audio software (Loopback, BlackHole)

**Backup:** Take manual notes. After fixing, re-record the next meeting.

---

#### Incident: "Transcription Stops Mid-Meeting"

**Severity:** P3

**Immediate actions:**
1. Check: is the computer awake? (Sleep kills transcription)
2. Right-click Granola icon > **Restart Granola**
3. Reopen your note — transcription may resume
4. If using Bluetooth: switch to wired audio or built-in speakers

**Root cause:** Granola stops transcription after ~15 minutes of no detected audio. Bluetooth devices can cause intermittent dropouts.

---

#### Incident: "Enhancement/Processing Failed"

**Severity:** P3

**Immediate actions:**
1. Wait 15 minutes — long meetings take longer to process
2. Check internet connectivity
3. Check [status.granola.ai](https://status.granola.ai) for service issues
4. Restart Granola and reopen the note
5. Click **Enhance Notes** again

**If still failing after 30 minutes:** The transcript was captured but enhancement may be queued. Submit support ticket with the meeting date/time.

---

#### Incident: "Integration Not Syncing" (Slack/Notion/HubSpot)

**Severity:** P3

**Immediate actions:**
1. Settings > Integrations > check the target integration status
2. Disconnect and reconnect the integration
3. Re-share the note manually
4. For Zapier: check Zap history at zapier.com for errors

**Common causes:**
| Integration | Likely Cause | Fix |
|-------------|-------------|-----|
| Slack | Bot removed from channel | `/invite @Granola` in the channel |
| Notion | Database deleted | Reconnect (new database created) |
| HubSpot | OAuth token expired | Reconnect in Settings |
| Zapier | Connection expired | Re-authenticate Granola in Zapier |

---

#### Incident: "Granola Service Outage" (P1)

**Severity:** P1 Critical

**Immediate actions:**
1. Confirm at [status.granola.ai](https://status.granola.ai)
2. Switch to **backup note-taking** immediately:
   - Open a text editor or Google Doc
   - Take manual notes for active meetings
   - Notes can be combined with future Granola captures manually
3. Communicate to your team via Slack:

```
:rotating_light: Granola is currently experiencing a service outage.

Status: https://status.granola.ai
Impact: Meeting recordings and AI enhancement are unavailable.

Workaround: Take notes manually in Google Docs or your preferred editor.
I'll update when service is restored.

Next update: [time + 30 min]
```

4. Subscribe to status updates at status.granola.ai
5. Resume normal operation when status returns to Operational

### Step 3 — Escalation Path

```
Level 1: User Self-Service
  → Restart Granola, check permissions, verify audio
  → Time: 5 minutes

Level 2: IT Support / Team Admin
  → Run debug bundle (granola-debug-bundle)
  → Check org-wide status, verify SSO/SCIM
  → Time: 15-30 minutes

Level 3: Granola Support
  → Submit ticket at help.granola.ai
  → Attach debug bundle
  → Enterprise: Priority support, dedicated contact
  → Time: 1-24 hours depending on severity

Level 4: Granola Engineering (P1 only)
  → Escalated by Granola Support for service outages
  → Status page updates provided by Granola team
```

### Step 4 — Post-Incident Review

After resolution, document:

```markdown
## Post-Incident Report

**Date:** YYYY-MM-DD
**Severity:** P1/P2/P3/P4
**Duration:** [start time] — [resolution time]
**Impact:** [# users affected, # meetings missed]

**Timeline:**
- HH:MM — Issue first reported
- HH:MM — Triage and severity assigned
- HH:MM — Workaround communicated
- HH:MM — Root cause identified
- HH:MM — Fix applied / service restored

**Root Cause:** [description]
**Resolution:** [what fixed it]
**Prevention:** [what to change to prevent recurrence]
**Action Items:**
- [ ] [who] [what] [by when]
```

## Output
- Incident triaged and severity assigned
- Remediation applied or workaround enabled
- Stakeholders notified with status updates
- Post-incident review documented with prevention actions

## Error Handling

| Scenario | First Response |
|----------|---------------|
| Can't reach status.granola.ai | Check your internet; try from phone network |
| Restart doesn't fix recording | Force quit (`pkill -9 Granola`), clear caches, relaunch |
| Multiple users reporting same issue | Likely P1/P2 — check status page, post to team Slack |
| Issue persists after all troubleshooting | Create debug bundle, submit to help@granola.ai |

## Resources
- [Granola Status Page](https://status.granola.ai)
- [Help Center](https://help.granola.ai)
- [Transcription Troubleshooting](https://docs.granola.ai/help-center/troubleshooting/transcription-issues)
- [Granola Updates (Known Issues)](https://www.granola.ai/updates)

## Next Steps
Proceed to `granola-data-handling` for data export, retention, and GDPR compliance.
